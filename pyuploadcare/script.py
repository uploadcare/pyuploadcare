from pyuploadcare.api import FilesAPI
from pyuploadcare.auth import UploadcareSimpleAuth


auth = UploadcareSimpleAuth(
    public_key="5d5bb5639e3f2df33674", secret_key="6e141dffbf0e0727359d"
)
files_api = FilesAPI(base_url="https://api.uploadcare.com/", auth=auth)
print(list(files_api.list()))
