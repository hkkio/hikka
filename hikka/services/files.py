from hikka.services.models.file import File
from hikka.services.models.user import User
from hikka.tools import storage

class FileService:
    @classmethod
    def create(cls, name: str, account: User) -> File:
        file = File(account=account, name=name)
        file.save()
        return file

    @classmethod
    def get_by_name(cls, name: str):
        file = File.objects().filter(name=name).first()
        return file

    @classmethod
    def destroy(cls, file: File):
        if file:
            if not file.is_link():
                if file.uploaded and file.path:
                    fs = storage.init_fs()
                    fs.rm(file.storage())

                file.delete()
