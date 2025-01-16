from pathlib import Path
from gopro2gpx import gopro2gpx
import os
import pytest

dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'


class Args(object):
    def __init__(self):
        self.binary = False
        self.skip = False
        self.skip_dop = False
        self.dop_limit = 2000
        self.verbose = 0
        self.files = []
        self.outputfile = None
        self.gpx = False
        self.kml = False
        self.csv = False


@pytest.mark.parametrize("sample_bin", ['fusion.bin',
                                        'hero05.bin',
                                        'hero06+ble.bin',
                                        'hero06.bin',
                                        'hero07.bin',
                                        'hero11.bin',
                                        'hero13.bin',
                                        'karma.bin'])
def test_sample_set(tmp_path: Path, sample_bin: str):

    samples_dir = dir_path + '../samples/'

    output_file_prefix = sample_bin.replace('.bin', '')
    
    args = Args()
    args.files = [os.path.normpath(samples_dir + sample_bin)]
    args.outputfile = os.path.normpath(tmp_path / output_file_prefix)
    args.binary = True
    args.verbose = 2    # leading to output of the bin file we already use as sample data
    start_bin_filename = args.files[0]
    result_bin_filename = os.path.normpath(tmp_path / (output_file_prefix + '.00.bin'))
    expected_gpx_filename = start_bin_filename.replace('.bin','.gpx')
    result_gpx_filename = os.path.normpath(tmp_path / (output_file_prefix + '.gpx'))
    expected_kml_filename = expected_gpx_filename.replace('.gpx', '.kml')
    result_kml_filename = result_gpx_filename.replace('.gpx', '.kml')
    expected_csv_filename = expected_gpx_filename.replace('.gpx', '.csv')
    result_csv_filename = result_gpx_filename.replace('.gpx', '.csv')
    gopro2gpx.main_core(args)
    
    # Check output bin file
    s0 = open(start_bin_filename, 'rb').read()
    s1 = open(result_bin_filename, 'rb').read()
    assert s0 == s1,f'{sample_bin} bin'

    # Check output gpx file
    s0 = open(expected_gpx_filename, 'r').read()
    s1 = open(result_gpx_filename, 'r').read()
    assert s0 == s1,f'{sample_bin} gpx'        
    # Check output kml file
    s0 = open(expected_kml_filename, 'r').read()
    s1 = open(result_kml_filename, 'r').read()
    assert s0 == s1,f'{sample_bin} kml'

    # Check output csv file
    s0 = open(expected_csv_filename, 'r').read()
    s1 = open(result_csv_filename, 'r').read()
    assert s0 == s1,f'{sample_bin} csv'
