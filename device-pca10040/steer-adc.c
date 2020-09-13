/**
 * Copyright (c) 2018 Keith Wakeham
 *
 * All rights reserved.
 *
 *
 */

#include "steer-adc.h"
#include "app_timer.h"
#include "nrf_log.h"
#include "nrf_log_ctrl.h"
#include "nrf_log_default_backends.h"
#include "nrf_saadc.h"
#include "nrfx_saadc.h"

#define SAMPLING_INTERVAL APP_TIMER_TICKS(100)

APP_TIMER_DEF(m_sampling_timer);

static nrf_saadc_value_t m_buffer_pool[2];
int16_t                  sample = 0;

bool converting = false;
bool flag_float_angle = false;

// Set to true to zero out the steerer with the next adc reading
bool    zero_out = true;
int32_t zero_offset = 0;

// Max amount of turn allowed
#define MAX_STEER_ANGLE (35)

// used to make sure we don't move around when we're close to center of joystick
#define ZERO_FLOOR 1

// 14 bits
#define MAX_ADC_RESOLUTION 16384

#ifdef BOARD_PCA10040
#define STEERER_PIN NRF_SAADC_INPUT_AIN0
#elif BOARD_PCA10059
#define STEERER_PIN NRF_SAADC_INPUT_AIN7
#endif

void saadc_callback(nrfx_saadc_evt_t const *p_event)
{
    if (p_event->type ==
        NRFX_SAADC_EVT_DONE)  // Capture offset calibration complete event
    {
        converting = false;
        if (zero_out)
        {
            zero_out = false;

            zero_offset = (MAX_ADC_RESOLUTION / 2) - m_buffer_pool[0];
            NRF_LOG_INFO("Zero %d %d", m_buffer_pool[0], zero_offset);
        }
    }
    else if (p_event->type == NRFX_SAADC_EVT_CALIBRATEDONE)
    {
        // Nothing, not calibrating
    }
}

void sampling_timer_callback(void *p_context)
{
    flag_float_angle = true;
    ret_code_t err_code;
    err_code = nrfx_saadc_buffer_convert(&m_buffer_pool[0], 1);
    APP_ERROR_CHECK(err_code);
    err_code = nrfx_saadc_sample();
    APP_ERROR_CHECK(err_code);
}

void steering_init(void)
{
    NRF_LOG_INFO("steer init");
    ret_code_t          err_code;
    nrfx_saadc_config_t saadc_config = {
        .resolution = (nrf_saadc_resolution_t)NRF_SAADC_RESOLUTION_14BIT,
        .oversample = (nrf_saadc_oversample_t)NRFX_SAADC_CONFIG_OVERSAMPLE,
        .interrupt_priority = NRFX_SAADC_CONFIG_IRQ_PRIORITY,
        .low_power_mode = NRFX_SAADC_CONFIG_LP_MODE};

    err_code = nrfx_saadc_init(&saadc_config, saadc_callback);
    APP_ERROR_CHECK(err_code);

    nrf_saadc_channel_config_t channel_config_steer =
        NRFX_SAADC_DEFAULT_CHANNEL_CONFIG_SE(STEERER_PIN);
    channel_config_steer.gain =
        NRF_SAADC_GAIN1_5;  // this is measured against either vdd/4 or vcore =
                            // 0.6v.

    nrfx_saadc_channel_init(0, &channel_config_steer);
    APP_ERROR_CHECK(err_code);

    err_code = nrfx_saadc_buffer_convert(&m_buffer_pool[0], 1);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_create(&m_sampling_timer, APP_TIMER_MODE_REPEATED,
                                sampling_timer_callback);
    APP_ERROR_CHECK(err_code);

    err_code = app_timer_start(m_sampling_timer, SAMPLING_INTERVAL, NULL);
    APP_ERROR_CHECK(err_code);
}

void steering_convert(void)
{
    ret_code_t err_code;
    converting = true;
    err_code = nrfx_saadc_sample();
    APP_ERROR_CHECK(err_code);
}

void steering_display_value(void) { NRF_LOG_INFO("read: %d, ", sample); }

//
float get_angle(void)
{
    float steering_angle = 0;

    steering_angle =
        (((m_buffer_pool[0] + zero_offset) / (float)MAX_ADC_RESOLUTION) *
         (MAX_STEER_ANGLE * 2)) -
        MAX_STEER_ANGLE;

    if (fabsf(steering_angle) < ZERO_FLOOR)
    {
        steering_angle = 0;
    }

    return steering_angle;
}
