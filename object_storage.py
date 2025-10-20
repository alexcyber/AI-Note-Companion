import boto3
from datetime import timezone
from mimetypes import guess_type

class ObjectStorage:
    def __init__(self):
        import load_environment
        self.env = load_environment.load_env()
        self.s3 = boto3.client('s3')
        self.bucket_name = self.env['S3_BUCKET_NAME']
        self.s3_parent_path = self.env['S3_PARENT_FOLDER']

    def document_upload(self, file_obj, rel_obj_path, filename):
        try:
            # Construct the full S3 key (path + filename)
            s3_key = f"{self.s3_parent_path}/{rel_obj_path}/{filename}" if rel_obj_path else f"{self.s3_parent_path}/{filename}"
            
            # Upload the file
            # For Streamlit UploadedFile, we can directly use the file object
            self.s3.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': file_obj.type if hasattr(file_obj, 'type') else 'application/octet-stream'
                }
            )
            
            # Generate the file URL
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            print(f"Successfully uploaded {filename} to s3://{self.bucket_name}/{s3_key}")
            return True, file_url
            
        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            print(error_msg)
            return False, error_msg

    def document_delete(self, rel_obj_path):
        response = self.s3.delete_object(Bucket=self.bucket_name, Key=f"{self.s3_parent_path}/{rel_obj_path}")
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        print(f"Delete: {self.bucket_name}/{self.s3_parent_path}/{rel_obj_path}")
        print(f"Status code: {status_code}")




    def get_objects(self, rel_obj_path: str = ""):
        try:
            files = []

            paginate_kwargs = {"Bucket": self.bucket_name}
            if rel_obj_path:
                # Ensure trailing slash if you're treating it like a "folder"
                paginate_kwargs["Prefix"] = f"{self.s3_parent_path}/{rel_obj_path}"
            else:
                paginate_kwargs["Prefix"] = f"{self.s3_parent_path}"
            print(rel_obj_path)
            print(f"Getting objects from {paginate_kwargs["Prefix"]}")
            paginator = self.s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(**paginate_kwargs):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    name = key.split('/')[-1] or key  # avoid empty name for "folder" keys
                    mime, _ = guess_type(name)
                    files.append({
                        "id": obj.get('ETag', '').strip('"'),
                        "name": name,
                        "size": obj['Size'],
                        "type": mime or "application/octet-stream",
                        "uploaded_at": obj['LastModified'].astimezone(timezone.utc).isoformat(),
                        "url": f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
                    })
            return files
        except Exception as e:
            raise RuntimeError(f"Failed to list s3 bucket: {e}") from e

if __name__ == "__main__":

    obj_store = ObjectStorage()
    files = obj_store.get_objects("files")
    print(files)
