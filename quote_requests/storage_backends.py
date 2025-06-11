from storages.backends.s3boto3 import S3Boto3Storage


class QuoteImageStorage(S3Boto3Storage):
    location = 'quote-images'
    file_overwrite = False
