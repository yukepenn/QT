"""Integer codes embedded in strategy signal arrays (Numba-era compatibility).

Accounting belongs in ``src.execution``; these are **labels only** for
``sig_target_mode`` / array columns that still use int8 codes.
"""

from __future__ import annotations

import numpy as np

# target_mode_code: 0 = none, 1 = fixed_r, 2 = fixed_price
TM_NONE = np.int8(0)
TM_FIXED_R = np.int8(1)
TM_FIXED_PX = np.int8(2)

__all__ = ["TM_NONE", "TM_FIXED_R", "TM_FIXED_PX"]
