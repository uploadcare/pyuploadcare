# coding: utf-8
from __future__ import unicode_literals
import os
import json
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from tempfile import NamedTemporaryFile

from mock import patch, MagicMock, Mock

from pyuploadcare import conf
from pyuploadcare.exceptions import InvalidRequestError
from pyuploadcare.ucare_cli import (
    ucare_argparser, get_file, store_files, delete_files, main,
    create_group
)
from pyuploadcare.api_resources import File
from pyuploadcare.ucare_cli.sync import (
    sync_files, save_file_locally, TrackedFileList, SyncSession
)
from .utils import MockResponse, MockListResponse, api_response_from_file


def arg_namespace(arguments_str):
    return ucare_argparser().parse_args(arguments_str.split())


class UcareGetTest(unittest.TestCase):

    @patch('requests.sessions.Session.request', autospec=True)
    def test_get_by_uuid(self, request):
        request.return_value = MockResponse(status=200)

        get_file(arg_namespace('get 6c5e9526-b0fe-4739-8975-72e8d5ee6342'))

        self.assertEqual(
            request.mock_calls[0][1][1:],
            ('GET', 'https://api.uploadcare.com/files/6c5e9526-b0fe-4739-8975-72e8d5ee6342/')
        )

    @patch('requests.sessions.Session.request', autospec=True)
    def test_get_by_cdn_url(self, request):
        request.return_value = MockResponse(status=200)

        get_file(arg_namespace('get https://ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/'))

        self.assertEqual(
            request.mock_calls[0][1][1:],
            ('GET', 'https://api.uploadcare.com/files/6c5e9526-b0fe-4739-8975-72e8d5ee6342/')
        )


class UcareStorageOperationsMixin(object):
    method_name = None  # e.g store or delete

    def test_parse_wait_arg(self):
        args = arg_namespace(
            '{0} --wait 6c5e9526-b0fe-4739-8975-72e8d5ee6342'.format(
                self.method_name))
        self.assertTrue(args.wait)

    def test_wait_is_true_by_default(self, *args):
        args = arg_namespace(
            '{0} 6c5e9526-b0fe-4739-8975-72e8d5ee6342'.format(
                self.method_name))
        self.assertTrue(args.wait)

    def test_parse_no_wait_arg(self):
        args = arg_namespace(
            '{0} --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342'.format(
                self.method_name))
        self.assertFalse(args.wait)

    @patch('pyuploadcare.ucare_cli.FilesStorage')
    def test_one_file(self, FilesStorage_):
        args = arg_namespace(
            '{0} --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342'.format(
                self.method_name))

        storage = MagicMock()
        FilesStorage_.return_value = storage

        self.func(args)

        FilesStorage_.assert_called_with(
            ['6c5e9526-b0fe-4739-8975-72e8d5ee6342'])

        self.assertTrue(getattr(storage, self.method_name).called)

    @patch('pyuploadcare.ucare_cli.FilesStorage')
    def test_several_files(self, FilesStorage_):
        args = arg_namespace(
            '{0} --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342 '
            '6c5e9526-b0fe-4739-8975-72e8d5ee6341'.format(
                self.method_name))

        storage = MagicMock()
        FilesStorage_.return_value = storage

        self.func(args)

        FilesStorage_.assert_called_with(
            ['6c5e9526-b0fe-4739-8975-72e8d5ee6342',
             '6c5e9526-b0fe-4739-8975-72e8d5ee6341'])

        self.assertTrue(getattr(storage, self.method_name).called)


class UcareStoreTest(UcareStorageOperationsMixin, unittest.TestCase):
    method_name = 'store'

    @property
    def func(self):
        return store_files


class UcareDeleteTest(UcareStorageOperationsMixin, unittest.TestCase):
    method_name = 'delete'

    @property
    def func(self):
        return delete_files


class UcareCommonArgsTest(unittest.TestCase):

    def setUp(self):
        conf.pub_key = None
        conf.secret = None

        conf.api_version = '0.4'
        conf.api_base = 'https://api.uploadcare.com/'
        conf.upload_base = 'https://upload.uploadcare.com/'

        conf.verify_api_ssl = True
        conf.verify_upload_ssl = True

    def tearDown(self):
        self.setUp()

    @patch('requests.sessions.Session.request', autospec=True)
    def test_change_pub_key(self, request):
        request.return_value = MockListResponse()

        main(arg_namespace('--pub_key demopublickey list_files'))

        self.assertEqual(conf.pub_key, 'demopublickey')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_change_secret(self, request):
        request.return_value = MockListResponse()

        main(arg_namespace('--secret demosecretkey list_files'))

        self.assertEqual(conf.secret, 'demosecretkey')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_change_api_base(self, request):
        request.return_value = MockListResponse()

        main(arg_namespace(
            '--api_base https://uploadcare.com/api/ list_files'))

        self.assertEqual(conf.api_base, 'https://uploadcare.com/api/')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_change_upload_base(self, request):
        request.return_value = MockListResponse()

        main(arg_namespace(
            '--upload_base https://uploadcare.com/upload/ list_files'))

        self.assertEqual(conf.upload_base, 'https://uploadcare.com/upload/')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_change_verify_api_ssl(self, request):
        request.return_value = MockListResponse()

        main(arg_namespace('list_files'))
        self.assertTrue(conf.verify_api_ssl)

        main(arg_namespace('--no_check_api_certificate list_files'))
        self.assertFalse(conf.verify_api_ssl)

    @patch('requests.sessions.Session.request', autospec=True)
    def test_change_verify_upload_ssl(self, request):
        request.return_value = MockListResponse()

        main(arg_namespace('list_files'))
        self.assertTrue(conf.verify_upload_ssl)

        main(arg_namespace('--no_check_upload_certificate list_files'))
        self.assertFalse(conf.verify_upload_ssl)

    @patch('requests.sessions.Session.request', autospec=True)
    def test_change_api_version(self, request):
        request.return_value = MockListResponse()

        main(arg_namespace('--api_version 0.777 list_files'))

        self.assertEqual(conf.api_version, '0.777')


class UcareCommonConfigFileTest(unittest.TestCase):

    def setUp(self):
        self.tmp_config_file = NamedTemporaryFile(mode='w+t', delete=False)

    def tearDown(self):
        conf.pub_key = None
        conf.secret = None

        conf.api_base = 'https://api.uploadcare.com/'
        conf.upload_base = 'https://upload.uploadcare.com/'

        conf.verify_api_ssl = True
        conf.verify_upload_ssl = True

    @patch('requests.sessions.Session.request', autospec=True)
    def test_use_pub_key_from_config_file(self, request):
        request.return_value = MockListResponse()

        self.tmp_config_file.write(
            '[ucare]\n'
            'pub_key = demopublickey'
        )
        self.tmp_config_file.close()

        main(arg_namespace('list_files'), [self.tmp_config_file.name])

        self.assertEqual(conf.pub_key, 'demopublickey')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_redefine_pub_key_by_second_config_file(self, request):
        request.return_value = MockListResponse()

        self.tmp_config_file.write(
            '[ucare]\n'
            'pub_key = demopublickey'
        )
        self.tmp_config_file.close()

        second_tmp_conf_file = NamedTemporaryFile(mode='w+t', delete=False)
        second_tmp_conf_file.write(
            '[ucare]\n'
            'pub_key = demopublickey_modified'
        )
        second_tmp_conf_file.close()

        main(arg_namespace('list_files'),
             [self.tmp_config_file.name, second_tmp_conf_file.name])

        self.assertEqual(conf.pub_key, 'demopublickey_modified')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_use_available_pub_key_from_config_files(self, request):
        request.return_value = MockListResponse()

        self.tmp_config_file.write(
            '[ucare]\n'
            'pub_key = demopublickey'
        )
        self.tmp_config_file.close()

        second_tmp_conf_file = NamedTemporaryFile(mode='w+t', delete=False)
        second_tmp_conf_file.write(
            '[ucare]\n'
            'secret = demosecretkey'
        )
        second_tmp_conf_file.close()

        main(arg_namespace('list_files'),
             [self.tmp_config_file.name, second_tmp_conf_file.name])

        self.assertEqual(conf.pub_key, 'demopublickey')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_redefine_config_pub_key_by_args(self, request):
        request.return_value = MockListResponse()

        self.tmp_config_file.write(
            '[ucare]\n'
            'pub_key = demopublickey'
        )
        self.tmp_config_file.close()

        main(arg_namespace('--pub_key pub list_files'),
             [self.tmp_config_file.name])

        self.assertEqual(conf.pub_key, 'pub')

    @patch('requests.sessions.Session.request', autospec=True)
    def test_load_verify_api_ssl_false_value_from_config(self, request):
        request.return_value = MockListResponse()

        self.tmp_config_file.write(
            '[ucare]\n'
            'verify_api_ssl = false'
        )
        self.tmp_config_file.close()

        main(arg_namespace('list_files'), [self.tmp_config_file.name])

        self.assertFalse(conf.verify_api_ssl)

    @patch('requests.sessions.Session.request', autospec=True)
    def test_load_verify_api_ssl_true_value_from_config(self, request):
        request.return_value = MockListResponse()

        self.tmp_config_file.write(
            '[ucare]\n'
            'verify_api_ssl = true'
        )
        self.tmp_config_file.close()

        main(arg_namespace('list_files'), [self.tmp_config_file.name])

        self.assertTrue(conf.verify_api_ssl)

    @patch('requests.sessions.Session.request', autospec=True)
    def test_redefine_config_verify_api_ssl_by_args(self, request):
        request.return_value = MockListResponse()

        self.tmp_config_file.write(
            '[ucare]\n'
            'verify_api_ssl = true'
        )
        self.tmp_config_file.close()

        main(arg_namespace('--no_check_api_certificate list_files'),
             [self.tmp_config_file.name])

        self.assertFalse(conf.verify_api_ssl)


class CreateFileGroupTest(unittest.TestCase):

    @patch('requests.sessions.Session.request', autospec=True)
    def test_uuid_and_cdn_url(self, request):
        json_response = b"""{
            "id": "0513dda0-582f-447d-846f-096e5df9e2bb~2",
            "files_count": 2,
            "files": [
                {"uuid": "44fc352e-7503-4826-b87b-a137404b9c53"},
                {"uuid": "a771f854-c2cb-408a-8c36-71af77811f3b"}
            ]
        }
        """
        request.return_value = MockResponse(status=200, data=json_response)

        create_group(arg_namespace(
            'create_group 44fc352e-7503-4826-b87b-a137404b9c53'
            ' https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/'
        ))

        self.assertEqual(
            request.mock_calls[0][1][1:],
            ('POST', 'https://upload.uploadcare.com/group/')
        )


@patch('pyuploadcare.ucare_cli.sync.save_file_locally', autospec=True)
@patch('os.makedirs', autospec=True)
@patch('os.path.exists', autospec=True)
@patch('requests.sessions.Session.request', autospec=True)
class UcareSyncTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(UcareSyncTestCase, cls).setUpClass()
        # Disable session restore
        cls.promt_patch = patch('pyuploadcare.ucare_cli.sync.promt')
        cls.promt = cls.promt_patch.start()
        cls.promt.return_value = False

    @classmethod
    def tearDownClass(cls):
        super(UcareSyncTestCase, cls).tearDownClass()
        cls.promt_patch.stop()

    @property
    def default_response(self):
        return MockListResponse.from_file('list_files.json')

    def test_created_directory_for_upload(self, request, exists, makedirs,
                                          save_file_locally):
        exists.return_value = False
        request.return_value = self.default_response
        makedirs.return_value = None

        diraname = 'diraname'

        sync_files(arg_namespace('sync {0}'.format(diraname)))

        self.assertEqual(len(makedirs.mock_calls), 9)
        self.assertTrue(diraname in makedirs.call_args[0])

    def test_file_exists_and_replace_flag(self, request, exists, makedirs,
                                          save_file_locally):
        exists.return_value = True
        request.return_value = self.default_response

        sync_files(arg_namespace('sync'))
        self.assertEqual(len(save_file_locally.mock_calls), 0)

        sync_files(arg_namespace('sync --replace'))
        self.assertEqual(len(save_file_locally.mock_calls), 9)

    def test_http_error(self, request, exists, makedirs, save_file_locally):
        request.return_value = self.default_response
        request.return_value.status_code = 400

        with self.assertRaises(InvalidRequestError):
            sync_files(arg_namespace('sync'))
        self.assertEqual(len(save_file_locally.mock_calls), 0)

    def test_uuids(self, request, exists, makedirs, save_file_locally):
        uuids = ('e16f669c-ecde-421b-8a0c-f6023d25b1e3',
                 'e16f669c-ecde-421b-8a0c-f6023d25b133')
        request.return_value = MockResponse.from_file('single_file.json')
        exists.return_value = False

        sync_files(arg_namespace('sync --uuids {0}'.format(' '.join(uuids))))
        self.assertEqual(len(save_file_locally.mock_calls), 2)

    def test_patterns_works(self, request, exists, makedirs,
                            save_file_locally):
        exists.return_value = False
        response = request.return_value = self.default_response

        sync_files(arg_namespace("sync ${uuid}${ext}"))

        self.assertEqual(len(save_file_locally.mock_calls), 9)

        expected_filenames = sorted('{0}{1}'.format(
            a['uuid'], os.path.splitext(a['original_filename'])[-1].lower()
        ) for a in response.json()['results'])

        filenames = sorted(b[1][0] for b in save_file_locally.mock_calls)

        self.assertListEqual(expected_filenames, filenames)

    @patch('requests.sessions.Session.get', autospec=True)
    def test_effects_works(self, get, request, exists, makedirs,
                           save_file_locally):
        exists.return_value = False
        response = request.return_value = self.default_response
        effects = "-/resize/200x200/"
        not_image_uuid = 'a4a79b35-01ed-4e83-ad5c-6bf155a31ed5'

        sync_files(arg_namespace("sync --effects={0}".format(effects)))

        self.assertEqual(save_file_locally.call_count, 9)
        self.assertEqual(get.call_count, 9)

        for call in get.call_args_list:
            url = call[0][1]

            # Check that effects don't applied on non-image
            if not_image_uuid in url:
                self.assertFalse(url.endswith(effects))

            # And applied on images
            else:
                self.assertTrue(url.endswith(effects))
                self.assertTrue('/-/-/' not in url)


class SaveFileLocallyTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_file = NamedTemporaryFile(mode='wb', delete=False)

    def tearDown(self):
        os.remove(self.tmp_file.name)

    def test_zero_filesize(self):
        response = Mock()
        response.iter_content.return_value = '1 2 3'.encode('utf-8').split()

        save_file_locally(self.tmp_file.name, response, 0)
        with open(self.tmp_file.name, 'r') as f:
            self.assertEqual(f.read(), '123')


@patch('pyuploadcare.ucare_cli.sync.promt', autospec=True)
class TrackedFileListTestCase(unittest.TestCase):
    def test_iteration_over_uuids(self, promt):
        promt.return_value = False

        uuids = ['e16f669c-ecde-421b-8a0c-f6023d25b1e3',
                 'e16f669c-ecde-421b-8a0c-f6023d25b133']

        file_list = TrackedFileList(uuids=uuids)

        with SyncSession(file_list) as files:
            for uuid, file_obj in zip(uuids, list(files)):
                self.assertIsInstance(file_obj, File)
                self.assertEqual(file_obj.uuid, uuid)

            # Tracking of handled files works
            self.assertListEqual(files.handled_uuids, uuids)

    def test_uuid_error(self, promt):
        """ Session saved if error happened.
        """
        promt.return_value = False

        uuids = ['e16f669c-ecde-421b-8a0c-f6023d25b1e3',
                 'e16f669c-ecde-421b-8a0c-f6023d25b133']

        file_list = TrackedFileList(uuids=uuids)
        session1 = SyncSession(file_list)

        with session1 as files:
            with self.assertRaises(ValueError):
                for i, file in enumerate(files):
                    if i > 0:
                        raise ValueError
                    self.assertEqual(file.uuid, uuids[0])

        # Restore the session
        promt.return_value = True
        session2 = SyncSession(file_list)
        with session2 as restored_files:
            # Old and restored sessions has an equal state
            self.assertListEqual(file_list.handled_uuids,
                                 restored_files.handled_uuids)

            # Iteration continued
            for file in files:
                self.assertEqual(file.uuid, uuids[1])

        # After successful iteration the serialized session is deleted
        self.assertFalse(os.path.exists(session2.session_filepath))

    @staticmethod
    def _rest_request_side_effect(method, url):
        """ Fake API response. In total 3 pages: page=0, page=1, page=2
        3 files per page.
        """
        files = json.loads(
            api_response_from_file('list_files.json').decode('utf-8'))

        # First iteration
        if not url.startswith('/page='):
            return dict(results=files[:3], next='/page=1')

        page = int(url.strip('/page='))

        if page == 1:
            return dict(results=files[3:6], next='/page=2')

        return dict(results=files[6:9], next=None)

    # UUIDs from the list_files.json
    list_files_uuids = [
        # page=0
        "e16f669c-ecde-421b-8a0c-f6023d25b1e3",
        "ff77605d-ac18-4140-9912-cf58d9d8da98",
        "11e3f3de-ee6e-4f19-b924-988da86951a4",
        # page=1
        "683ba092-639a-4b66-b98b-33f77c34b030",
        "da5f7610-213a-42b1-944a-922a2e5510ee",
        "bbd35834-5a6f-4fb2-a628-7ddc1c444f2b",
        # page=2
        "dd536a15-a6a2-43a3-8eae-04513e66118d",
        "a4a79b35-01ed-4e83-ad5c-6bf155a31ed5",
        "1a73ee75-56fa-4143-8ff0-f9f44f3cacd8",
    ]

    @patch('pyuploadcare.ucare_cli.sync.rest_request', autospec=True)
    def test_iteration_over_files(self, rest_request, promt):
        promt.return_value = False
        rest_request.side_effect = self._rest_request_side_effect

        with SyncSession(TrackedFileList()) as files:
            for uuid, file_obj in zip(self.list_files_uuids, files):
                self.assertIsInstance(file_obj, File)
                self.assertEqual(file_obj.uuid, uuid)

            # The last page saved
            self.assertEqual(files.last_page_url, '/page=2')

    @patch('pyuploadcare.ucare_cli.sync.rest_request', autospec=True)
    def test_iteration_over_files_error(self, rest_request, promt):
        promt.return_value = False
        rest_request.side_effect = self._rest_request_side_effect

        file_list = TrackedFileList()

        session1 = SyncSession(file_list)
        with session1 as files:
            with self.assertRaises(ValueError):
                # Raise an error on the page=1
                for i, file in enumerate(files):
                    if i > 4:
                        raise ValueError
                    self.assertEqual(file.uuid, self.list_files_uuids[i])

            # Saved correct page
            self.assertEqual(files.last_page_url, '/page=1')

            # Several files from the page=1 already handled
            self.assertListEqual(files.handled_uuids,
                                 self.list_files_uuids[3:i])

        # Restore the session
        promt.return_value = True
        session2 = SyncSession(file_list)
        files_left = self.list_files_uuids[i:]

        with session2 as files:
            # Old and restored sessions has equal state
            self.assertEqual(file_list.last_page_url, files.last_page_url)
            self.assertListEqual(file_list.handled_uuids, files.handled_uuids)

            for i, file in enumerate(files):
                self.assertEqual(file.uuid, files_left[i])

        # After successful iteration the serialized session is deleted
        self.assertFalse(os.path.exists(session2.session_filepath))
