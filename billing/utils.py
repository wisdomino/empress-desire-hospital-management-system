from decimal import Decimal

DEFAULT_HMO_COVERAGE = Decimal("0.80")  # 80%

def split_amount(total, is_hmo: bool):
    total = Decimal(total)
    if not is_hmo:
        return total, Decimal("0.00")
    hmo_share = (total * DEFAULT_HMO_COVERAGE).quantize(Decimal("0.01"))
    patient_share = (total - hmo_share).quantize(Decimal("0.01"))
    return patient_share, hmo_share
