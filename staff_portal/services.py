
import logging
from django.utils import timezone
from .models import Job

logger = logging.getLogger(__name__)


def create_subscription_job(agreement, package):
    """
    Creates a Job in the staff portal for a new subscription.
    :param agreement: ServiceAgreement instance
    :param package: ServicePackage instance
    :return: Job instance
    :raises: ValueError if required data is missing
    """
    if not agreement or not agreement.property:
        raise ValueError("Cannot create job: agreement or property is missing.")

    job = Job.objects.create(
        title=f"New job for subscription: {package.name}",
        property=agreement.property,
        service_agreement=agreement,
        description=f"Process new subscription agreement ID {agreement.id}",
        status='PENDING',
        scheduled_date=agreement.start_date or timezone.now().date(),
    )

    logger.info(f"Job {job.id} created for agreement {agreement.id}")
    return job