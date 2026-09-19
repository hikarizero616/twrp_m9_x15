#
# Copyright (C) 2026 The Android Open Source Project
# Copyright (C) 2026 SebaUbuntu's TWRP device tree generator
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common Omni stuff.
$(call inherit-product, vendor/omni/config/common.mk)

# Inherit from k53_cb_m1_x15 device
$(call inherit-product, device/alps/k53_cb_m1_x15/device.mk)

PRODUCT_DEVICE := k53_cb_m1_x15
PRODUCT_NAME := omni_k53_cb_m1_x15
PRODUCT_BRAND := alps
PRODUCT_MODEL := m9_x15
PRODUCT_MANUFACTURER := alps

PRODUCT_GMS_CLIENTID_BASE := android-alps

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRIVATE_BUILD_DESC="full_k53_cb_m1_x15-user 8.1.0 O11019 1716970408 test-keys"

BUILD_FINGERPRINT := alps/full_k53_cb_m1_x15/k53_cb_m1_x15:8.1.0/O11019/1716970408:user/test-keys
