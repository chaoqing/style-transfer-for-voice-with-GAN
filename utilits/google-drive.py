import sys
import apiclient
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload
import httplib2
import oauth2client
from oauth2client import file as oauth2client_file
from json import dumps as json_dumps

# Retry transport and file IO errors.
RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)

# Number of times to retry failed downloads.
NUM_RETRIES = 5

# Number of bytes to send/receive in each request.
CHUNKSIZE = 8 * 1024 * 1024

# Mimetype to use if one can't be guessed from the file extension.
DEFAULT_MIMETYPE = 'application/octet-stream'

def print_with_carriage_return(s):
    sys.stdout.write('\r' + s)
    sys.stdout.flush()

def handle_progressless_iter(error, progressless_iters):
    if progressless_iters > NUM_RETRIES:
        print('Failed to make progress for too many consecutive iterations.')
        raise error

    sleeptime = random.random() * (2**progressless_iters)
    print(('Caught exception (%s). Sleeping for %s seconds before retry #%d.'
         % (str(error), sleeptime, progressless_iters)))
    time.sleep(sleeptime)


class StrStorage(oauth2client_file.Storage):
    """
    I just do not want to put the credentials into file system
    """

    def __init__(self, filename, content):
        super(StrStorage, self).__init__(filename)
        self._create_file_if_needed()
        self._content = content

    def locked_get(self):
        try:
            credentials = oauth2client.client.Credentials.new_from_json(self._content)
            credentials.set_store(self)
        except ValueError:
            pass
        return credentials

    def locked_put(self, credentials):
        self._create_file_if_needed()
        oauth2client._helpers.validate_file(self._filename)
        f = open(self._filename, 'w')
        f.write('')
        f.close()

        
class googleDrive(object):
    def __init__(self, credentials, config = None):
        self.service = self.get_authenticated_service(credentials)
        
    def get_authenticated_service(self, credentials):
        store = StrStorage('credentials.json', credentials)
        return apiclient.discovery.build('drive', 'v3', http=store.get().authorize(httplib2.Http()))
    
    def list(self, filename=None):
        query = "name='{}'".format(filename) if filename else None
        
        page_token = None
        while True:
            response = self.service.files().list(q=query,
                                                  spaces='drive',
                                                  fields='nextPageToken, files(id, name)',
                                                  pageToken=page_token).execute()
            
            items = response.get('files', [])
            if filename and items:
                return items[0].get('id')
            for file in items:
                print('Found file: %s (%s)' % (file.get('name'), file.get('id')))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        
    def upload(self, filename):
        print('Building upload request...')
        media = MediaFileUpload(filename, chunksize=CHUNKSIZE, resumable=True)
        if not media.mimetype():
            media = MediaFileUpload(filename, DEFAULT_MIMETYPE, resumable=True)
            
        request = self.service.files().create(media_body=media, body={'name': filename})
        print('Uploading file: %s' % (filename))

        progressless_iters = 0
        response = None
        while response is None:
            error = None
            try:
                progress, response = request.next_chunk()
                if progress:
                    print_with_carriage_return('Upload %d%%' % (100 * progress.progress()))
            except HttpError as err:
                error = err
                if err.resp.status < 500:
                    raise
            except RETRYABLE_ERRORS as err:
                error = err

            if error:
                progressless_iters += 1
                handle_progressless_iter(error, progressless_iters)
            else:
                progressless_iters = 0

        print('\nUpload complete!')
        print(json_dumps(response))

    def download(self, filename):
        print('Building download request...')
        f = open(filename, 'wb')
        request = self.service.files().get_media(fileId=self.list(filename))
        media = MediaIoBaseDownload(f, request, chunksize=CHUNKSIZE)

        print('Downloading file: %s' % (filename))

        progressless_iters = 0
        done = False
        while not done:
            error = None
            try:
                progress, done = media.next_chunk()
                if progress:
                    print_with_carriage_return(
                        'Download %d%%.' % int(progress.progress() * 100))
            except HttpError as err:
                error = err
                if err.resp.status < 500:
                    raise
            except RETRYABLE_ERRORS as err:
                error = err

            if error:
                progressless_iters += 1
                handle_progressless_iter(error, progressless_iters)
            else:
                progressless_iters = 0
            
        f.close()

        print('\nDownload complete!')
