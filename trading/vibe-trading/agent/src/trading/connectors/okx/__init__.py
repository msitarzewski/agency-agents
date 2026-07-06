"""OKX trading connector.

Read-only account/market access in Layer A via the optional ``python-okx`` SDK
(``AccountAPI`` + ``TradeAPI`` + ``MarketAPI`` over REST). A ``broker_sdk``
transport. Order placement (paper and mandate-gated live) is layered on top in
later phases; no place/cancel method is exposed here.

Paper-vs-live separation is namespace + header based: OKX demo (paper) keys live
in a separate key namespace and the ``x-simulated-trading`` header (driven by the
SDK ``flag`` argument — ``"1"`` demo, ``"0"`` live) selects the environment. OKX
returns NO response field echoing demo/live, so there is no hard self-verifying
guard; the discriminator is the configured ``flag`` plus best-effort UID pinning
(``expected_uid``). The selected profile (and thus the flag) is recorded as
``paper`` on every payload and never flipped implicitly.
"""
