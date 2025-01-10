import os

import ipdb
from vuln_service.info_read import parse_log_info
from vuln_service.utils import get_data_dir


def test_log_parse() -> None:
    data_dir = get_data_dir()
    fpath = os.path.join(data_dir, "np_fuzz_log")
    with open(fpath, "r") as f:
        log_content = f.read()
    ipdb.set_trace()
    parse_log_info(log_content)
