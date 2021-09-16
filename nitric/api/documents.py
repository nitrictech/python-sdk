#
# Copyright (c) 2021 Nitric Technologies Pty Ltd.
#
# This file is part of Nitric Python 3 SDK.
# See https://github.com/nitrictech/python-sdk for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, AsyncIterator, Union, Any, Tuple

from grpclib import GRPCError

from nitric.api.const import MAX_SUB_COLLECTION_DEPTH
from nitric.api.exception import exception_from_grpc_error
from nitricapi.nitric.document.v1 import (
    DocumentServiceStub,
    Collection as CollectionMessage,
    Key as KeyMessage,
    Expression as ExpressionMessage,
    ExpressionValue,
    Document as DocumentMessage,
)

from nitric.utils import new_default_channel, _dict_from_struct, _struct_from_dict

NIL_DOC_ID = ""


class CollectionDepthException(Exception):
    """The max depth of document sub-collections has been exceeded."""

    pass


@dataclass(frozen=True, order=True)
class DocumentRef:
    """A reference to a document in a collection."""

    _documents: Documents
    parent: CollectionRef
    id: str

    def collection(self, name: str) -> CollectionRef:
        """
        Return a reference to a sub-collection of this document.

        This is currently only supported to one level of depth.
        e.g. Documents().collection('a').doc('b').collection('c').doc('d') is valid,
        Documents().collection('a').doc('b').collection('c').doc('d').collection('e') is invalid (1 level too deep).
        """
        current_depth = self.parent.sub_collection_depth()
        if current_depth >= MAX_SUB_COLLECTION_DEPTH:
            # Collection nesting is only supported to a maximum depth.
            raise CollectionDepthException(
                f"sub-collections supported to a depth of {MAX_SUB_COLLECTION_DEPTH}, "
                f"attempted to create new collection with depth {current_depth + 1}"
            )
        return CollectionRef(_documents=self._documents, name=name, parent=self)

    async def get(self) -> Document:
        """Retrieve the contents of this document, if it exists."""
        try:
            response = await self._documents._stub.get(key=_doc_ref_to_wire(self))
            return _document_from_wire(documents=self._documents, message=response.document)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def set(self, content: dict):
        """
        Set the contents of this document.

        If the document exists it will be updated, otherwise a new document will be created.
        """
        try:
            await self._documents._stub.set(
                key=_doc_ref_to_wire(self),
                content=_struct_from_dict(content),
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def delete(self):
        """Delete this document, if it exists."""
        try:
            await self._documents._stub.delete(
                key=_doc_ref_to_wire(self),
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)


def _document_from_wire(documents: Documents, message: DocumentMessage) -> Document:
    ref = _doc_ref_from_wire(documents=documents, message=message.key)

    return Document(
        _ref=ref,
        content=_dict_from_struct(message.content),
    )


def _doc_ref_to_wire(ref: DocumentRef) -> KeyMessage:
    return KeyMessage(id=ref.id, collection=_collection_to_wire(ref.parent))


def _doc_ref_from_wire(documents: Documents, message: KeyMessage) -> DocumentRef:
    return DocumentRef(
        _documents=documents,
        id=message.id,
        parent=_collection_from_wire(documents=documents, message=message.collection),
    )


def _collection_to_wire(ref: CollectionRef) -> CollectionMessage:
    if ref.is_sub_collection():
        return CollectionMessage(name=ref.name, parent=_doc_ref_to_wire(ref.parent) if ref.parent else None)
    return CollectionMessage(name=ref.name)


def _collection_from_wire(documents: Documents, message: CollectionMessage) -> CollectionRef:
    return CollectionRef(
        _documents=documents,
        name=message.name,
        parent=_doc_ref_from_wire(documents=documents, message=message.parent) if message.parent else None,
    )


@dataclass(frozen=True, order=True)
class CollectionRef:
    """A reference to a collection of documents."""

    _documents: Documents
    name: str
    parent: Union[DocumentRef, None] = field(default_factory=lambda: None)

    def doc(self, doc_id: str) -> DocumentRef:
        """Return a reference to a document in the collection."""
        return DocumentRef(_documents=self._documents, parent=self, id=doc_id)

    def collection(self, name: str) -> CollectionGroupRef:
        """
        Return a reference to a sub-collection of this document.

        This is currently only supported to one level of depth.
        e.g. Documents().collection('a').collection('b').doc('c') is valid,
        Documents().collection('a').doc('b').collection('c').collection('d') is invalid (1 level too deep).
        """
        current_depth = self.sub_collection_depth()
        if current_depth >= MAX_SUB_COLLECTION_DEPTH:
            # Collection nesting is only supported to a maximum depth.
            raise CollectionDepthException(
                f"sub-collections supported to a depth of {MAX_SUB_COLLECTION_DEPTH}, "
                f"attempted to create new collection with depth {current_depth + 1}"
            )
        return CollectionGroupRef(_documents=self._documents, name=name, parent=self)

    def query(
        self,
        paging_token: Any = None,
        limit: int = 0,
        expressions: Union[Expression, List[Expression]] = None,
    ) -> QueryBuilder:
        """Return a query builder scoped to this collection."""
        return QueryBuilder(
            documents=self._documents,
            collection=self,
            paging_token=paging_token,
            limit=limit,
            expressions=[expressions] if isinstance(expressions, Expression) else expressions,
        )

    def sub_collection_depth(self) -> int:
        """Return the depth of this collection, which is a count of the parents above this collection."""
        if not self.is_sub_collection():
            return 0
        else:
            return self.parent.parent.sub_collection_depth() + 1

    def is_sub_collection(self):
        """Return True if this collection is a sub-collection of a document in another collection."""
        return self.parent is not None


@dataclass(frozen=True, order=True)
class CollectionGroupRef:
    """A reference to a collection group."""

    _documents: Documents
    name: str
    parent: Union[CollectionRef, None] = field(default_factory=lambda: None)

    def query(
        self,
        paging_token: Any = None,
        limit: int = 0,
        expressions: Union[Expression, List[Expression]] = None,
    ) -> QueryBuilder:
        """Return a query builder scoped to this collection."""
        return QueryBuilder(
            documents=self._documents,
            collection=self.to_collection_ref(),
            paging_token=paging_token,
            limit=limit,
            expressions=[expressions] if isinstance(expressions, Expression) else expressions,
        )

    def sub_collection_depth(self) -> int:
        """Return the depth of this collection group, which is a count of the parents above this collection."""
        if not self.is_sub_collection():
            return 0
        else:
            return self.parent.sub_collection_depth() + 1

    def is_sub_collection(self):
        """Return True if this collection is a sub-collection of a document in another collection."""
        return self.parent is not None

    def to_collection_ref(self):
        """Return this collection group as a collection ref."""
        return CollectionRef(
            self._documents,
            self.name,
            DocumentRef(
                self._documents,
                self.parent,
                NIL_DOC_ID,
            ),
        )

    @staticmethod
    def from_collection_ref(collectionRef: CollectionRef, documents: Documents) -> CollectionGroupRef:
        """Return a collection ref as a collection group."""
        if collectionRef.parent is not None:
            return CollectionGroupRef(
                documents,
                collectionRef.name,
                CollectionGroupRef.from_collection_ref(
                    collectionRef.parent,
                    documents,
                ),
            )


class Operator(Enum):
    """Valid query expression operators."""

    less_than = "<"
    greater_than = ">"
    less_than_or_equal = "<="
    greater_than_or_equal = ">="
    equals = "=="
    starts_with = "startsWith"


class _ExpressionBuilder:
    """Builder for creating query expressions using magic methods."""

    def __init__(self, operand):
        self._operand = operand

    def __eq__(self, other) -> Expression:
        return Expression(self._operand, Operator.equals, other)

    def __lt__(self, other) -> Expression:
        return Expression(self._operand, Operator.less_than, other)

    def __le__(self, other) -> Expression:
        return Expression(self._operand, Operator.less_than_or_equal, other)

    def __gt__(self, other) -> Expression:
        return Expression(self._operand, Operator.greater_than, other)

    def __ge__(self, other) -> Expression:
        return Expression(self._operand, Operator.greater_than_or_equal, other)

    def eq(self, other) -> Expression:
        return self == other

    def lt(self, other) -> Expression:
        return self < other

    def le(self, other) -> Expression:
        return self <= other

    def gt(self, other) -> Expression:
        return self > other

    def ge(self, other) -> Expression:
        return self >= other

    def starts_with(self, match) -> Expression:
        return Expression(self._operand, Operator.starts_with, match)


def condition(name: str) -> _ExpressionBuilder:
    """
    Construct a query expressions builder, for convenience.

    Expression builders in turn provides magic methods for constructing expressions.

    e.g. prop('first_name') == 'john' is equivalent to Expression('first_name, '=', 'john')

    Supported operations are ==, <, >, <=, >=, .starts_with()
    """
    return _ExpressionBuilder(operand=name)


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

    _ref: DocumentRef
    content: dict

    @property
    def id(self):
        """Return the document's unique id."""
        return self._ref.id

    @property
    def collection(self) -> CollectionRef:
        """Return the CollectionRef for the collection that contains this document."""
        return self._ref.parent

    @property
    def ref(self):
        """Return the DocumentRef for this document."""
        return self._ref


@dataclass(frozen=True, order=True)
class QueryResultsPage:
    """Represents a page of results from a query."""

    paging_token: any = field(default_factory=lambda: None)
    documents: List[Document] = field(default_factory=lambda: [])

    def has_more_pages(self) -> bool:
        """Return false if the page token is None or empty (both represent no more pages)."""
        return bool(self.paging_token)


class QueryBuilder:
    """Document query builder for retrieving documents from a collection based on filters."""

    _documents: Documents
    _collection: CollectionRef
    _paging_token: Any
    _limit: int
    _expressions: List[Expression]

    def __init__(
        self,
        documents: Documents,
        collection: CollectionRef,
        paging_token: Any = None,
        limit: int = 0,
        expressions: List[Expression] = None,
    ):
        """Construct a new QueryBuilder."""
        self._documents = documents
        self._collection = collection
        self._paging_token = paging_token
        self._limit = limit  # default to unlimited.
        if expressions is None:
            self._expressions = []
        else:
            self._expressions = expressions

    def _flat_expressions(self, expressions) -> List[Expression]:
        """Process possible inputs for .where() into a flattened list of expressions."""
        if isinstance(expressions, tuple) and len(expressions) == 3 and isinstance(expressions[0], str):
            # handle the special case where an expression was passed in as its component arguments.
            # e.g. .where('age', '<', 30) instead of .where(condition('age') > 30)
            return [Expression(*expressions)]
        if isinstance(expressions, Expression):
            # when a single expression is received, wrap in a list and return it
            return [expressions]
        else:
            # flatten lists of lists into single dimension list of expressions
            exps = []
            for exp in expressions:
                exps = exps + self._flat_expressions(exp)
            return exps

    def where(
        self,
        *expressions: Union[
            Expression, List[Expression], Union[str, Operator, int, bool, Tuple[str, Union[str, Operator], Any]]
        ],
    ) -> QueryBuilder:
        """
        Add a filter expression to the query.

        :param expressions: a single expression or a set of expression args or a variadic/tuple/list of expressions.

        Examples
        --------
            .where('age', '>', 20)
            .where(condition('age') > 20)
            .where(condition('age').gt(20))
            .where(
                condition('age') > 20,
                condition('age') < 50,
            )
            .where(
                [
                    condition('age') > 20,
                    condition('age') < 50,
                ]
            )
            .where(
                ('age', '>', 20),
                ('age', '<', 50),
            )

        """
        for expression in self._flat_expressions(expressions):
            self._expressions.append(expression)
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

        try:
            async for result in self._documents._stub.query_stream(
                collection=_collection_to_wire(self._collection),
                expressions=self._expressions_to_wire(),
                limit=self._limit,
            ):
                yield _document_from_wire(documents=self._documents, message=result.document)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def fetch(self) -> QueryResultsPage:
        """
        Fetch a single page of results.

        If a page has been fetched previously, a token can be provided via paging_from(), to fetch the subsequent pages.
        """
        try:
            results = await self._documents._stub.query(
                collection=_collection_to_wire(self._collection),
                expressions=self._expressions_to_wire(),
                limit=self._limit,
                paging_token=self._paging_token,
            )

            return QueryResultsPage(
                paging_token=results.paging_token if results.paging_token else None,
                documents=[
                    _document_from_wire(documents=self._documents, message=result) for result in results.documents
                ],
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

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
