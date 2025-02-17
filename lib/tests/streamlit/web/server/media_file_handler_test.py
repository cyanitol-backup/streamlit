# Copyright 2018-2022 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import mock

import tornado.testing
import tornado.web
from tornado.httpclient import HTTPResponse

from streamlit.runtime.media_file_manager import media_file_manager
from streamlit.web.server.media_file_handler import MediaFileHandler


class MediaFileHandlerTest(tornado.testing.AsyncHTTPTestCase):
    def setUp(self) -> None:
        super().setUp()
        # Clear the MediaFileManager before each test
        media_file_manager._files_by_id.clear()
        media_file_manager._files_by_session_and_coord.clear()

    def get_app(self) -> tornado.web.Application:
        return tornado.web.Application(
            [("/media/(.*)", MediaFileHandler, {"path": ""})]
        )

    def _fetch_file(self, filename) -> HTTPResponse:
        return self.fetch(f"/media/{filename}", method="GET")

    @mock.patch(
        "streamlit.runtime.media_file_manager._get_session_id",
        return_value="mock_session_id",
    )
    def test_media_file(self, _) -> None:
        """Requests for media files in MediaFileManager should succeed."""
        # Add a media file and read it back
        media_file = media_file_manager.add(b"mock_data", "video/mp4", "mock_coords")
        rsp = self._fetch_file(f"{media_file.id}{media_file.extension}")

        self.assertEqual(200, rsp.code)
        self.assertEqual(b"mock_data", rsp.body)
        self.assertEqual("video/mp4", rsp.headers["Content-Type"])
        self.assertEqual(str(len(b"mock_data")), rsp.headers["Content-Length"])

    @mock.patch(
        "streamlit.runtime.media_file_manager._get_session_id",
        return_value="mock_session_id",
    )
    def test_downloadable_file(self, _) -> None:
        """Downloadable files get an additional 'Content-Disposition' header
        that includes their user-specified filename.
        """
        # Add a downloadable file with a filename
        media_file = media_file_manager.add(
            b"mock_data",
            "video/mp4",
            "mock_coords",
            file_name="MockVideo.mp4",
            is_for_static_download=True,
        )
        rsp = self._fetch_file(f"{media_file.id}{media_file.extension}")

        self.assertEqual(200, rsp.code)
        self.assertEqual(b"mock_data", rsp.body)
        self.assertEqual("video/mp4", rsp.headers["Content-Type"])
        self.assertEqual(str(len(b"mock_data")), rsp.headers["Content-Length"])
        self.assertEqual(
            'attachment; filename="MockVideo.mp4"', rsp.headers["Content-Disposition"]
        )

    def test_invalid_file(self) -> None:
        """Requests for invalid files fail with 404."""
        rsp = self._fetch_file("invalid_media_file")
        self.assertEqual(404, rsp.code)
