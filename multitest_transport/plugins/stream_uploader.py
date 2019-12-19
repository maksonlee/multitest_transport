# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""An UploadMedia which allows streaming upload from local to remote.

The reason that we need this class is because the original library
apiclient.http.MediaIoBaseUpload doesn't provide the functionality for one
to upload from local to remote in streaming way. If one wants to upload a
5G file but we only have 1G memory, the original library forces us to
read the entire file into a buffer, and upload that buffer as a whole. This
will overwhelm our computer and crash the process. Thus, this class through
inheriting the class and overriding the key methods, it modifies the original
behavior and allows uploading in chunk to become a reality.
"""

import io
import urllib2
import apiclient.http


DEFAULT_CHUNK_SIZE = 512*1024


class MediaUpload(apiclient.http.MediaIoBaseUpload):
  """Media uploader."""

  def __init__(self,
               url,
               total_size,
               mimetype=None,
               chunksize=DEFAULT_CHUNK_SIZE,
               resumable=False):
    self._total_size = total_size
    self._url = url
    super(MediaUpload, self).__init__(fd=io.BytesIO(),
                                      mimetype=mimetype,
                                      chunksize=chunksize,
                                      resumable=resumable)

  def size(self):
    """Size of upload.

    Returns:
      Size of the body
    """
    return self._total_size

  def getbytes(self, begin, length):
    """Get bytes from the media.

    Args:
      begin: int, offset from beginning of file.
      length: int, number of bytes to read, starting at begin.

    Returns:
      A string of bytes read. May be shorted than length if EOF was reached
      first.
    """
    try:
      headers = {"Range": "bytes=%s-%s" % (begin, begin + length - 1)}
      src = urllib2.urlopen(urllib2.Request(self._url, headers=headers))
      content = src.read()
      src.close()
    except urllib2.HTTPError as e:
      raise e
    return content

  def has_stream(self):
    """Does the underlying upload support a streaming interface.

    Overriding the original method so that we can perform streaming ourselves.
    Returns:
       False
    """
    return False
