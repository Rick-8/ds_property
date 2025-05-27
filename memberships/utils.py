from memberships.models import ServiceAgreement

# Define tier rankings for comparison
TIER_RANKS = {
    'SINGLE': 1,
    'DOUBLE': 2,
}

def upgrade_service_package(user, property_obj, new_package):
    """
    Upgrade or create a ServiceAgreement only if it's an upgrade.
    Returns (success: bool, message: str).
    """
    try:
        current_agreement = ServiceAgreement.objects.get(user=user, property=property_obj, active=True)
        current_tier = current_agreement.service_package.tier
    except ServiceAgreement.DoesNotExist:
        current_agreement = None
        current_tier = None

    new_tier = new_package.tier

    if current_agreement is None:
        # No current agreement, create one
        ServiceAgreement.objects.create(
            user=user,
            property=property_obj,
            service_package=new_package,
            active=True,
        )
        return True, "Service agreement created successfully."

    if TIER_RANKS[new_tier] > TIER_RANKS[current_tier]:
        # Upgrade allowed: deactivate old, create new agreement
        current_agreement.active = False
        current_agreement.save()

        ServiceAgreement.objects.create(
            user=user,
            property=property_obj,
            service_package=new_package,
            active=True,
        )
        return True, "Service package upgraded successfully."

    if TIER_RANKS[new_tier] == TIER_RANKS[current_tier]:
        return False, "You already have this package."

    return False, "Downgrades are not allowed. Please contact the office."
