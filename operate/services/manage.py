#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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
"""Service manager."""

import logging
import typing as t
from pathlib import Path

from aea.helpers.base import IPFSHash
from aea.helpers.logging import setup_logger
from autonomy.chain.base import registry_contracts

from operate.keys import Key, KeysManager
from operate.ledger.profiles import CONTRACTS, OLAS, STAKING
from operate.services.protocol import OnChainManager
from operate.services.service import (
    Deployment,
    OnChainData,
    OnChainState,
    OnChainUserParams,
    Service,
)
from operate.wallet.master import MasterWalletManager


# pylint: disable=redefined-builtin

OPERATE = ".operate"
CONFIG = "config.json"
SERVICES = "services"
KEYS = "keys"
DEPLOYMENT = "deployment"
CONFIG = "config.json"
KEY = "master-key.txt"
KEYS_JSON = "keys.json"
DOCKER_COMPOSE_YAML = "docker-compose.yaml"
SERVICE_YAML = "service.yaml"


class ServiceManager:
    """Service manager."""

    def __init__(
        self,
        path: Path,
        keys_manager: KeysManager,
        wallet_manager: MasterWalletManager,
        logger: t.Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialze service manager

        :param path: Path to service storage.
        :param keys: Keys manager.
        :param master_key_path: Path to master key.
        :param logger: logging.Logger object.
        """
        self.path = path
        self.keys_manager = keys_manager
        self.wallet_manager = wallet_manager
        self.logger = logger or setup_logger(name="operate.manager")

    def setup(self) -> None:
        """Setup service manager."""
        self.path.mkdir(exist_ok=True)

    @property
    def json(self) -> t.List[t.Dict]:
        """Returns the list of available services."""
        data = []
        for path in self.path.iterdir():
            service = Service.load(path=path)
            data.append(service.json)
        return data

    def get_on_chain_manager(self, service: Service) -> OnChainManager:
        """Get OnChainManager instance."""
        return OnChainManager(
            rpc=service.ledger_config.rpc,
            wallet=self.wallet_manager.load(service.ledger_config.type),
            contracts=CONTRACTS[service.ledger_config.chain],
        )

    def create_or_load(
        self,
        hash: str,
        rpc: t.Optional[str] = None,
        on_chain_user_params: t.Optional[OnChainUserParams] = None,
        keys: t.Optional[t.List[Key]] = None,
    ) -> Service:
        """
        Create or load a service

        :param hash: Service hash
        :param rpc: RPC string
        """
        path = self.path / hash
        if path.exists():
            return Service.load(path=path)

        if rpc is None:
            raise ValueError("RPC cannot be None when creating a new service")

        if on_chain_user_params is None:
            raise ValueError(
                "On-chain user parameters cannot be None when creating a new service"
            )

        return Service.new(
            hash=hash,
            keys=keys or [],
            rpc=rpc,
            storage=self.path,
            on_chain_user_params=on_chain_user_params,
        )

    def deploy_service_onchain(self, hash: str) -> None:
        """
        Deploy as service on-chain

        :param hash: Service hash
        """
        self.logger.info("Loading service")
        service = self.create_or_load(hash=hash)
        user_params = service.chain_data.user_params
        update = service.chain_data.token != -1
        keys = service.keys or [
            self.keys_manager.get(self.keys_manager.create())
            for _ in range(service.helper.config.number_of_agents)
        ]
        instances = [key.address for key in keys]
        ocm = self.get_on_chain_manager(service=service)
        if user_params.use_staking and not ocm.staking_slots_available(
            staking_contract=STAKING[service.ledger_config.chain]
        ):
            raise ValueError("No staking slots available")

        if user_params.use_staking:
            self.logger.info("Checking staking compatibility")
            required_olas = (
                user_params.olas_cost_of_bond + user_params.olas_required_to_stake
            )
            balance = (
                registry_contracts.erc20.get_instance(
                    ledger_api=ocm.ledger_api,
                    contract_address=OLAS[service.ledger_config.chain],
                )
                .functions.balanceOf(ocm.crypto.address)
                .call()
            )

            if balance < required_olas:
                raise ValueError(
                    "You don't have enough olas to stake, "
                    f"required olas: {required_olas}; your balance {balance}"
                )

        if service.chain_data.on_chain_state == OnChainState.NOTMINTED:
            self.logger.info("Minting service")
            service.chain_data.token = t.cast(
                int,
                ocm.mint(
                    package_path=service.service_path,
                    agent_id=user_params.agent_id,
                    number_of_slots=service.helper.config.number_of_agents,
                    cost_of_bond=(
                        user_params.olas_cost_of_bond
                        if user_params.use_staking
                        else user_params.cost_of_bond
                    ),
                    threshold=user_params.threshold,
                    nft=IPFSHash(user_params.nft),
                    update_token=service.chain_data.token if update else None,
                    token=(
                        OLAS[service.ledger_config.chain]
                        if user_params.use_staking
                        else None
                    ),
                ).get("token"),
            )
            service.chain_data.on_chain_state = OnChainState.MINTED
            service.store()
        else:
            self.logger.info("Service already minted")

        if service.chain_data.on_chain_state == OnChainState.MINTED:
            self.logger.info("Activating service")
            ocm.activate(
                service_id=service.chain_data.token,
                token=(
                    OLAS[service.ledger_config.chain]
                    if user_params.use_staking
                    else None
                ),
            )
            service.chain_data.on_chain_state = OnChainState.ACTIVATED
            service.store()
        else:
            self.logger.info("Service already activated")

        if service.chain_data.on_chain_state == OnChainState.ACTIVATED:
            self.logger.info("Registering service")
            ocm.register(
                service_id=service.chain_data.token,
                instances=instances,
                agents=[user_params.agent_id for _ in instances],
            )
            service.chain_data.on_chain_state = OnChainState.REGISTERED
            service.keys = keys
            service.store()
        else:
            self.logger.info("Service already registered")

        if service.chain_data.on_chain_state == OnChainState.REGISTERED:
            self.logger.info("Deploying service")
            ocm.deploy(
                service_id=service.chain_data.token,
                reuse_multisig=update,
                token=(
                    OLAS[service.ledger_config.chain]
                    if user_params.use_staking
                    else None
                ),
            )
            service.chain_data.on_chain_state = OnChainState.DEPLOYED
            service.store()
        else:
            self.logger.info("Service already deployed")

        info = ocm.info(token_id=service.chain_data.token)
        service.keys = keys
        service.chain_data = OnChainData(
            token=service.chain_data.token,
            instances=info["instances"],
            multisig=info["multisig"],
            staked=False,
            on_chain_state=service.chain_data.on_chain_state,
            user_params=service.chain_data.user_params,
        )
        service.store()

    def terminate_service_on_chain(self, hash: str) -> None:
        """
        Terminate service on-chain

        :param hash: Service hash
        """
        service = self.create_or_load(hash=hash)
        if service.chain_data.on_chain_state != OnChainState.DEPLOYED:
            self.logger.info("Cannot terminate service")
            return

        self.logger.info("Terminating service")
        ocm = self.get_on_chain_manager(service=service)
        ocm.terminate(
            service_id=service.chain_data.token,
            token=(
                OLAS[service.ledger_config.chain]
                if service.chain_data.user_params.use_staking
                else None
            ),
        )
        service.chain_data.on_chain_state = OnChainState.TERMINATED
        service.store()

    def unbond_service_on_chain(self, hash: str) -> None:
        """
        Unbond service on-chain

        :param hash: Service hash
        """
        service = self.create_or_load(hash=hash)
        if service.chain_data.on_chain_state != OnChainState.TERMINATED:
            self.logger.info("Cannot unbond service")
            return

        self.logger.info("Unbonding service")
        ocm = self.get_on_chain_manager(service=service)
        ocm.unbond(
            service_id=service.chain_data.token,
            token=(
                OLAS[service.ledger_config.chain]
                if service.chain_data.user_params.use_staking
                else None
            ),
        )
        service.chain_data.on_chain_state = OnChainState.UNBONDED
        service.store()

    def stake_service_on_chain(self, hash: str) -> None:
        """
        Stake service on-chain

        :param hash: Service hash
        """
        service = self.create_or_load(hash=hash)
        if not service.chain_data.user_params.use_staking:
            self.logger.info("Cannot stake service, `use_staking` is set to false")
            return

        if service.chain_data.staked:
            self.logger.info("Cannot stake service, it's already staked")
            return

        if service.chain_data.on_chain_state != OnChainState.DEPLOYED:
            self.logger.info("Cannot stake service, it's not in deployed state")
            return

        ocm = self.get_on_chain_manager(service=service)
        ocm.stake(
            service_id=service.chain_data.token,
            service_registry=CONTRACTS[service.ledger_config.chain]["service_registry"],
            staking_contract=STAKING[service.ledger_config.chain],
        )
        service.chain_data.staked = True
        service.store()

    def unstake_service_on_chain(self, hash: str) -> None:
        """
        Unbond service on-chain

        :param hash: Service hash
        """
        service = self.create_or_load(hash=hash)
        if not service.chain_data.user_params.use_staking:
            self.logger.info("Cannot unstake service, `use_staking` is set to false")
            return

        if not service.chain_data.staked:
            self.logger.info("Cannot unstake service, it's not staked")
            return

        ocm = self.get_on_chain_manager(service=service)
        ocm.unstake(
            service_id=service.chain_data.token,
            staking_contract=STAKING[service.ledger_config.chain],
        )
        service.chain_data.staked = False
        service.store()

    def fund_service(self, hash: str) -> None:
        """Fund service if required."""
        service = self.create_or_load(hash=hash)
        wallet = self.wallet_manager.load(ledger_type=service.ledger_config.type)
        ledger_api = wallet.ledger_api(chain_type=service.ledger_config.chain)
        agent_fund_requirement = service.chain_data.user_params.fund_requirements.agent

        self.logger.info("Funding agents")
        for key in service.keys:
            agent_balance = ledger_api.get_balance(address=key.address)
            if agent_balance < agent_fund_requirement:
                to_transfer = agent_fund_requirement - agent_balance
                self.logger.info(f"Transferring {to_transfer} units to {key.address}")
                wallet.transfer(
                    to=key.address,
                    amount=to_transfer,
                    chain_type=service.ledger_config.chain,
                )

        self.logger.info("Funding safe")
        safe_fund_requirement = service.chain_data.user_params.fund_requirements.safe
        safe_balanace = ledger_api.get_balance(wallet.safe)
        if safe_balanace < safe_fund_requirement:
            to_transfer = safe_fund_requirement - safe_balanace
            self.logger.info(f"Transferring {to_transfer} units to {wallet.safe}")
            wallet.transfer(
                to=t.cast(str, wallet.safe),
                amount=to_transfer,
                chain_type=service.ledger_config.chain,
            )

    def deploy_service_locally(self, hash: str, force: bool = True) -> Deployment:
        """
        Deploy service locally

        :param hash: Service hash
        :param force: Remove previous deployment and start a new one.
        """
        deployment = self.create_or_load(hash=hash).deployment
        deployment.build(force=force)
        deployment.start()
        return deployment

    def stop_service_locally(self, hash: str, delete: bool) -> Deployment:
        """
        Stop service locally

        :param hash: Service hash
        :param delete: Delete local deployment.
        """
        deployment = self.create_or_load(hash=hash).deployment
        deployment.stop()
        if delete:
            deployment.delete()
        return deployment

    def update_service(
        self,
        old_hash: str,
        new_hash: str,
        rpc: t.Optional[str] = None,
        on_chain_user_params: t.Optional[OnChainUserParams] = None,
    ) -> Service:
        """Update a service."""
        old_service = self.create_or_load(
            hash=old_hash,
        )
        self.unstake_service_on_chain(
            hash=old_hash,
        )
        self.terminate_service_on_chain(
            hash=old_hash,
        )
        self.unbond_service_on_chain(
            hash=old_hash,
        )
        ocm = self.get_on_chain_manager(service=old_service)
        owner, *_ = old_service.chain_data.instances
        ocm.swap(
            service_id=old_service.chain_data.token,
            multisig=old_service.chain_data.multisig,
            owner_key=str(self.keys_manager.get(key=owner).private_key),
        )

        new_service = self.create_or_load(
            hash=new_hash,
            rpc=rpc or old_service.ledger_config.rpc,
            on_chain_user_params=on_chain_user_params
            or old_service.chain_data.user_params,
        )
        new_service.keys = old_service.keys
        new_service.chain_data = old_service.chain_data
        new_service.ledger_config = old_service.ledger_config
        new_service.chain_data.on_chain_state = OnChainState.NOTMINTED
        new_service.store()

        self.deploy_service_onchain(hash=new_service.hash)
        old_service.delete()
        return new_service
