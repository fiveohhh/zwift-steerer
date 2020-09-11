/**
 * Copyright (c) 2018 Keith Wakeham
 *
 * All rights reserved.
 *
 *
 */

#ifndef STEERING_H
#define STEERING_H

#include <inttypes.h>
#include <math.h>
#include <stdint.h>

#include "app_error.h"
#include "nrfx_saadc.h"

#ifdef __cplusplus
extern "C"
{
#endif

    void saadc_callback(nrfx_saadc_evt_t const *p_event);

    void steering_init(void);

    void steering_convert(void);

    void steering_display_value(void);

    float get_angle(void);

    void saadc_execute(void);

#ifdef __cplusplus
}
#endif

#endif  // MPOS_H