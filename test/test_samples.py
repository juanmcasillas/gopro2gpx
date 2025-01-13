from gopro2gpx import gopro2gpx
import os

dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'


class Args(object):
    def __init__(self):
        self.binary = False
        self.skip = False
        self.skipDop = False
        self.dopLimit = 2000
        self.verbose = 0
        self.files = []
        self.outputfile = None



def test_sample_set():

    samples_dir = dir_path + '../samples/'

    sample_pairs = [
        ('fusion.bin', 'fusion.gpx'),
        ('hero05.bin', 'hero05.gpx'),
        ('hero06+ble.bin', 'hero06+ble.gpx'),
        ('hero06.bin', 'hero06.gpx'),
        ('hero07.bin', 'hero07.gpx'),
        ('hero11.bin', 'hero11.gpx'),
        ('karma.bin', 'karma.gpx'),
    ]

    print('dir_path: {}'.format(dir_path))

    for sample_bin, sample_gpx in sample_pairs:
        print(f'Testing {sample_bin} to {sample_gpx}:')

        output_file_prefix = sample_bin.replace('.bin', '')

        args = Args()
        args.files = [os.path.normpath(samples_dir + sample_bin)]
        args.outputfile = os.path.normpath(dir_path + output_file_prefix)
        args.binary = True
        args.verbose = 2

        expected_gpx_filename = os.path.normpath(samples_dir + sample_gpx)
        result_gpx_filename = os.path.normpath(dir_path + output_file_prefix + '.gpx')

        expected_kml_filename = expected_gpx_filename.replace('.gpx', '.kml')
        result_kml_filename = os.path.normpath(dir_path + output_file_prefix + '.kml')

        result_bin_filename = os.path.normpath(dir_path + output_file_prefix + '.00.bin')

        gopro2gpx.main_core(args)

        # Check output gpx file
        s0 = open(expected_gpx_filename, 'r').read()
        s1 = open(result_gpx_filename, 'r').read()
        assert(s0 == s1,f'{sample_bin} gpx')
        
        # Check output kml file
        s0 = open(expected_kml_filename, 'r').read()
        s1 = open(result_kml_filename, 'r').read()
        assert(s0 == s1,f'{sample_bin} kml')

        # On success, clean up test files
        os.remove(result_bin_filename)
        os.remove(result_gpx_filename)
        os.remove(result_kml_filename)
