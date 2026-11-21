"""支持 ``python -m cashbook`` 直接运行。"""

import sys

from cashbook.cli import main

if __name__ == "__main__":
    sys.exit(main())
