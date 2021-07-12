from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, AsyncIterator, Union

from nitric.proto.nitric.document.v1 import (
    DocumentServiceStub,
    Collection as CollectionMessage,
    Key as KeyMessage,
    Expression as ExpressionMessage,
    ExpressionValue,
    Document as DocumentMessage,
)
from nitric.utils import new_default_channel, _dict_from_struct, _struct_from_dict


@dataclass(frozen=True, order=True)
class DocumentRef:
    """A reference to a document in a collection."""

    _documents: Documents
    _collection: CollectionRef
    key: str

    def collection(self, name: str) -> CollectionRef:
        """
        Return a reference to a sub-collection of this document.

        This is currently only supported to one level of depth.
        e.g. Documents().collection('a').doc('b').collection('c').doc('d') is valid,
        Documents().collection('a').doc('b').collection('c').doc('d').collection('e') is invalid (1 level too deep).
        """
        if self._collection.is_sub_collection():
            # Collection nesting is currently unsupported, but may be included in a future enhancement.
            raise Exception("Currently, sub-collections may only be nested 1 deep")
        return CollectionRef(_documents=self._documents, name=name, parent=self)

    async def get(self) -> dict:
        """Retrieve the contents of this document, if it exists."""
        response = await self._documents._stub.get(key=KeyMessage(collection=self._collection._to_wire(), id=self.key))
        return _dict_from_struct(response.document.content)

    async def set(self, content: dict):
        """
        Set the contents of this document.

        If the document exists it will be updated, otherwise a new document will be created.
        """
        await self._documents._stub.set(
            key=KeyMessage(collection=self._collection._to_wire(), id=self.key),
            content=_struct_from_dict(content),
        )

    async def delete(self):
        """Delete this document, if it exists."""
        await self._documents._stub.delete(
            key=KeyMessage(collection=self._collection._to_wire(), id=self.key),
        )

    def _to_wire(self) -> KeyMessage:
        return KeyMessage(id=self.key, collection=self._collection._to_wire())


@dataclass(frozen=True, order=True)
class CollectionRef:
    """A reference to a collection of documents."""

    _documents: Documents
    name: str
    parent: Union[DocumentRef, None] = field(default_factory=lambda: None)

    def doc(self, key: str) -> DocumentRef:
        """Return a reference to a document in the collection."""
        return DocumentRef(_documents=self._documents, _collection=self, key=key)

    def query(self) -> QueryBuilder:
        """Return a query builder scoped to this collection."""
        return QueryBuilder(documents=self._documents, collection=self)

    def is_sub_collection(self):
        """Return True if this collection is a sub-collection of a document in another collection."""
        return self.parent is not None

    def _to_wire(self) -> CollectionMessage:
        if self.is_sub_collection():
            return CollectionMessage(name=self.name, parent=self.parent._to_wire())
        return CollectionMessage(name=self.name)


class Operator(Enum):
    """Valid query expression operators."""

    less_than = "<"
    greater_than = ">"
    less_than_or_equal = "<="
    greater_than_or_equal = ">="
    equals = "="
    starts_with = "startsWith"


@dataclass(order=True)
class Expression:
    """Query expressions, representing a boolean operation used for query filters."""

    operand: str
    operator: Union[Operator, str]
    value: Union[str, int, float, bool]

    def __post_init__(self):
        if isinstance(self.operator, str):
            # Convert string operators to their enum values
            self.operator = Operator(self.operator)

    def _value_to_expression_value(self):
        """Return an ExpressionValue message representation of the value of this expression."""
        if isinstance(self.value, str):
            return ExpressionValue(string_value=self.value)
        # Check bool before numbers, because booleans are numbers.
        if isinstance(self.value, bool):
            return ExpressionValue(bool_value=self.value)
        if isinstance(self.value, int):
            return ExpressionValue(int_value=self.value)
        if isinstance(self.value, float):
            return ExpressionValue(double_value=self.value)

    def _to_wire(self):
        """Return the Expression protobuf message representation of this expression."""
        return ExpressionMessage(
            operand=self.operand,
            operator=self.operator.value,
            value=self._value_to_expression_value(),
        )

    def __str__(self):
        return "{0} {1} {2}".format(self.operand, self.operator.name, self.value)


@dataclass(frozen=True, order=True)
class Document:
    """Represents a document and any associated metadata."""

    content: dict

    @staticmethod
    def _from_wire(message: DocumentMessage):
        """Convert a protobuf document message representation to a document object."""
        return Document(
            content=_dict_from_struct(message.content),
        )


@dataclass(frozen=True, order=True)
class QueryResultsPage:
    """Represents a page of results from a query."""

    paging_token: any = field(default_factory=lambda: None)
    documents: List[Document] = field(default_factory=lambda: [])


class QueryBuilder:
    """Document query builder for retrieving documents from a collection based on filter expressions."""

    _documents: Documents
    _collection: CollectionRef
    _paging_token: object
    _limit: int
    _expressions: List[Expression]

    def __init__(self, documents: Documents, collection: CollectionRef):
        """Construct a new QueryBuilder."""
        self._documents = documents
        self._collection = collection
        self._paging_token = None
        self._limit = 0  # default to unlimited.
        self._expressions = []

    def where(self, operand: str, operator: Union[Operator, str], value) -> QueryBuilder:
        """Add a filter expression to the query."""
        self._expressions.append(Expression(operand, operator, value))
        return self

    def page_from(self, token) -> QueryBuilder:
        """
        Set the paging token for the query.

        Used when requesting subsequent pages from a query.
        """
        self._paging_token = token
        return self

    def limit(self, limit: int) -> QueryBuilder:
        """Set the maximum number of results returned by this query."""
        if limit is None or not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a positive integer or 0 for unlimited.")
        self._limit = limit
        return self

    def _expressions_to_wire(self) -> List[ExpressionMessage]:
        """Return this queries' expressions as a list of their protobuf message representation."""
        return [expressions._to_wire() for expressions in self._expressions]

    async def stream(self) -> AsyncIterator[Document]:
        """Return all query results as a stream."""
        # TODO: add limit, expressions and paging token to query.
        if self._paging_token is not None:
            raise ValueError("page_from() should not be used with streamed queries.")

        async for result in self._documents._stub.query_stream(
            collection=self._collection._to_wire(),
            expressions=self._expressions_to_wire(),
            limit=self._limit,
        ):
            yield Document._from_wire(result.document)

    async def fetch(self) -> QueryResultsPage:
        """
        Fetch a single page of results.

        If a page has been fetched previously, a token can be provided via paging_from(), to fetch the subsequent pages.
        """
        results = await self._documents._stub.query(
            collection=self._collection._to_wire(),
            expressions=self._expressions_to_wire(),
            limit=self._limit,
            paging_token=self._paging_token,
        )

        return QueryResultsPage(
            paging_token=results.paging_token, documents=[Document._from_wire(result) for result in results.documents]
        )

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()

    def __str__(self):
        repr_str = "from {0}".format(str(self._collection))
        if self._paging_token:
            repr_str += ", paging token {0}".format(str(self._paging_token))
        if len(self._expressions):
            repr_str += ", where " + " and ".join([str(exp) for exp in self._expressions])
        if self._limit != 1:
            repr_str += ", limit to {0} results".format(self._limit)

        return "Query({0})".format(repr_str)

    def __repr__(self):
        repr_str = "Documents.collection({0}).query()".format(self._collection)
        if self._paging_token:
            repr_str += ".page_from({0})".format(self._paging_token)
        if len(self._expressions):
            repr_str += "".join([".where({0})".format(str(exp)) for exp in self._expressions])
        if self._limit != 1:
            repr_str += ".limit({0})".format(self._limit)

        return repr_str


class Documents(object):
    """
    Nitric client for interacting with document collections.

    This client insulates application code from stack specific event operations or SDKs.
    """

    _stub: DocumentServiceStub

    def __init__(self):
        """Construct a Nitric Document Client."""
        self._channel = new_default_channel()
        self._stub = DocumentServiceStub(channel=self._channel)

    def __del__(self):
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    def collection(self, name: str) -> CollectionRef:
        """Return a reference to a document collection."""
        return CollectionRef(_documents=self, name=name)
