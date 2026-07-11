# Copyright Notice:
# Copyright 2017-2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

import os
import sys

cur_dir = os.path.dirname( __file__ )
path_dir = os.path.abspath( os.path.join( cur_dir, os.path.pardir ) )
if path_dir not in sys.path:
    sys.path.insert( 0, path_dir )
