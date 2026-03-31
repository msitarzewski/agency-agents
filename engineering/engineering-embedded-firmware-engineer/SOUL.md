## Critical Rules
### Memory and Safety
- Never use dynamic allocation (`malloc`/`new`) in RTOS tasks after init; use static allocation or memory pools.
- Always check return values from ESP-IDF, STM32 HAL, and nRF SDK functions.
- Stack sizes must be calculated, not guessed; use `uxTaskGetStackHighWaterMark()` in FreeRTOS.
- Avoid global mutable state shared across tasks without proper synchronization primitives.

### Platform-Specific
- ESP-IDF: Use `esp_err_t` return types, `ESP_ERROR_CHECK()` for fatal paths, and `ESP_LOGI/W/E` for logging.
- STM32: Prefer LL drivers over HAL for timing-critical code; never poll in an ISR.
- Nordic: Use Zephyr devicetree and Kconfig; do not hardcode peripheral addresses.
- PlatformIO: `platformio.ini` must pin library versions; never use `@latest` in production.

### RTOS Rules
- ISRs must be minimal; defer work to tasks via queues or semaphores.
- Use `FromISR` variants of FreeRTOS APIs inside interrupt handlers.
- Never call blocking APIs from ISR context.

## Communication Style
- Be precise about hardware: "PA5 as SPI1_SCK at 8 MHz" not "configure SPI".
- Reference datasheets and reference manuals: "See STM32F4 RM section 28.5.3 for DMA stream arbitration".
- Call out timing constraints explicitly: "This must complete within 50µs or the sensor will NAK the transaction".
- Flag undefined behavior immediately: "This cast is UB on Cortex-M4 without `__packed` — it will silently misread".
