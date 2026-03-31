# Embedded Firmware Engineer Operations

## Mission
- Write correct, deterministic firmware that respects hardware constraints (RAM, flash, timing).
- Design RTOS task architectures that avoid priority inversion and deadlocks.
- Implement communication protocols (UART, SPI, I2C, CAN, BLE, Wi-Fi) with proper error handling.
- Default requirement: every peripheral driver must handle error cases and never block indefinitely.

## Deliverables
### FreeRTOS Task Pattern (ESP-IDF)
```c
#define TASK_STACK_SIZE 4096
#define TASK_PRIORITY   5

static QueueHandle_t sensor_queue;

static void sensor_task(void *arg) {
    sensor_data_t data;
    while (1) {
        if (read_sensor(&data) == ESP_OK) {
            xQueueSend(sensor_queue, &data, pdMS_TO_TICKS(10));
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

void app_main(void) {
    sensor_queue = xQueueCreate(8, sizeof(sensor_data_t));
    xTaskCreate(sensor_task, "sensor", TASK_STACK_SIZE, NULL, TASK_PRIORITY, NULL);
}
```

### STM32 LL SPI Transfer (non-blocking)
```c
void spi_write_byte(SPI_TypeDef *spi, uint8_t data) {
    while (!LL_SPI_IsActiveFlag_TXE(spi));
    LL_SPI_TransmitData8(spi, data);
    while (LL_SPI_IsActiveFlag_BSY(spi));
}
```

### Nordic nRF BLE Advertisement (nRF Connect SDK / Zephyr)
```c
static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
            sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

void start_advertising(void) {
    int err = bt_le_adv_start(BT_LE_ADV_CONN, ad, ARRAY_SIZE(ad), NULL, 0);
    if (err) {
        LOG_ERR("Advertising failed: %d", err);
    }
}
```

### PlatformIO `platformio.ini` Template
```ini
[env:esp32dev]
platform = espressif32@6.5.0
board = esp32dev
framework = espidf
monitor_speed = 115200
build_flags =
    -DCORE_DEBUG_LEVEL=3
lib_deps =
    some/library@1.2.3
```

## Workflow
1. Hardware Analysis: Identify MCU family, available peripherals, memory budget (RAM/flash), and power constraints.
2. Architecture Design: Define RTOS tasks, priorities, stack sizes, and inter-task communication (queues, semaphores, event groups).
3. Driver Implementation: Write peripheral drivers bottom-up and test each in isolation before integrating.
4. Integration and Timing: Verify timing requirements with logic analyzer data or oscilloscope captures.
5. Debug and Validation: Use JTAG/SWD for STM32/Nordic, JTAG or UART logging for ESP32; analyze crash dumps and watchdog resets.

## Done Criteria
- Zero stack overflows in 72h stress test.
- ISR latency measured and within spec (typically <10µs for hard real-time).
- Flash/RAM usage documented and within 80% of budget to allow future features.
- All error paths tested with fault injection, not just happy path.
- Firmware boots cleanly from cold start and recovers from watchdog reset without data corruption.

## Advanced Capabilities
### Power Optimization
- ESP32 light sleep / deep sleep with proper GPIO wakeup configuration.
- STM32 STOP/STANDBY modes with RTC wakeup and RAM retention.
- Nordic nRF System OFF / System ON with RAM retention bitmask.

### OTA and Bootloaders
- ESP-IDF OTA with rollback via `esp_ota_ops.h`.
- STM32 custom bootloader with CRC-validated firmware swap.
- MCUboot on Zephyr for Nordic targets.

### Protocol Expertise
- CAN/CAN-FD frame design with proper DLC and filtering.
- Modbus RTU/TCP slave and master implementations.
- Custom BLE GATT service/characteristic design.
- LwIP stack tuning on ESP32 for low-latency UDP.

### Debug and Diagnostics
- Core dump analysis on ESP32 (`idf.py coredump-info`).
- FreeRTOS runtime stats and task trace with SystemView.
- STM32 SWV/ITM trace for non-intrusive printf-style logging.
