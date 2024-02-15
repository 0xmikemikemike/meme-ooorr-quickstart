# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Ledger helpers."""

import typing as t

from operate.ledger.base import LedgerHelper
from operate.ledger.ethereum import Ethereum
from operate.ledger.solana import Solana
from operate.types import ChainType, LedgerType

ETHEREUM_RPC = "https://ethereum.publicnode.com"
GNOSIS_RPC = "https://rpc.gnosischain.com"
GOERLI_RPC = "https://ethereum-goerli.publicnode.com"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"


DEFAULT_RPCS = {
    ChainType.ETHEREUM: ETHEREUM_RPC,
    ChainType.GNOSIS: GNOSIS_RPC,
    ChainType.GOERLI: GOERLI_RPC,
    ChainType.SOLANA: SOLANA_RPC,
}

CHAIN_HELPERS: t.Dict[ChainType, t.Type[LedgerHelper]] = {
    ChainType.ETHEREUM: Ethereum,
    ChainType.GNOSIS: Ethereum,
    ChainType.GOERLI: Ethereum,
    ChainType.SOLANA: Solana,
}

LEDGER_HELPERS: t.Dict[LedgerType, t.Type[LedgerHelper]] = {
    LedgerType.ETHEREUM: Ethereum,
    LedgerType.SOLANA: Solana,
}

CURRENCY_DENOMS = {
    ChainType.ETHEREUM: "Wei",
    ChainType.GNOSIS: "xDai",
    ChainType.GOERLI: "GWei",
    ChainType.SOLANA: "Lamp",
}


def get_default_rpc(chain: ChainType) -> str:
    return DEFAULT_RPCS.get(chain, ETHEREUM_RPC)


def get_ledger_helper_by_chain(rpc: str, chain: ChainType) -> LedgerHelper:
    return CHAIN_HELPERS.get(chain, Ethereum)(rpc=rpc)


def get_ledger_helper_by_ledger(rpc: str, ledger: LedgerHelper) -> LedgerHelper:
    return LEDGER_HELPERS.get(ledger, Ethereum)(rpc=rpc)


def get_currency_denom(chain: ChainType):
    return CURRENCY_DENOMS.get(chain, "Wei")