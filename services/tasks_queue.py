from tasks.cloudinary_delete_tasks import delete_cloudinary_file

class TaskQueue:
    def enqueue_cloudinary_delete(self,public_id: str, resource_type: str):
        delete_cloudinary_file.delay(public_id, resource_type)