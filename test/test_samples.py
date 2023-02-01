from gopro2gpx import gopro2gpx
import os

dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'


class Args(object):
    def __init__(self):
        self.binary = False
        self.skip = False
        self.verbose = 0
        self.files = []
        self.outputfile = None


def test_sample_set():

    samples_dir = dir_path + '../samples/'

    sample_pairs = [
        ('fusion.bin', 'fusion.gpx'),
        ('gopro7.bin', 'gopro7.gpx'),
        ('hero5.bin', 'hero5.gpx'),
        ('hero6+ble.bin', 'hero6+ble.gpx'),
        ('hero6.bin', 'hero6.gpx'),
        ('karma.bin', 'karma.gpx'),
    ]

    print('dir_path: {}'.format(dir_path))

    for sample_bin, sample_gpx in sample_pairs:
        print('Testing {} to {}'.format(sample_bin, sample_gpx))

        output_file_prefix = sample_bin.replace('.bin', '')

        args = Args()
        args.files = [samples_dir + sample_bin]
        args.outputfile = dir_path + output_file_prefix
        args.binary = True
        args.verbose = 2

        expected_filename = samples_dir + sample_gpx
        result_gpx_filename = dir_path + output_file_prefix + '.gpx'
        result_bin_filename = dir_path + output_file_prefix + '.00.bin'

        gopro2gpx.main_core(args)

        # Check output bin file
        s0 = open(samples_dir + sample_bin, 'rb').read()
        s1 = open(result_bin_filename, 'rb').read()
        assert(s0 == s1)

        # Check output gpx file
        s0 = open(expected_filename).read()
        s1 = open(result_gpx_filename).read()
        assert(s0 == s1)

        # On success, clean up test files
        os.remove(result_bin_filename)
        os.remove(result_gpx_filename)


