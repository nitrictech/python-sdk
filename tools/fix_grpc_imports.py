import glob
import fileinput
import os

AUTO_GEN_PATH = '../nitric/proto/**/*_grpc.py'
REPLACE = 'from v1 import'
WITH = 'from . import'


def main():
    tools_dir = os.path.dirname(__file__)
    gen_dir = os.path.join(tools_dir, AUTO_GEN_PATH)
    grcp_paths = glob.glob(gen_dir)

    for path in grcp_paths:
        print('fixing imports in {}'.format(path))
        with fileinput.FileInput(path, inplace=True) as file:
            for line in file:
                print(line.replace(REPLACE, WITH), end='')


if __name__ == "__main__":
    main()
