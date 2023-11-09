"""LoadBalancingPolicy: Policy to select endpoint."""
import random
from typing import List, Optional

import fastapi

from sky import sky_logging

logger = sky_logging.init_logger(__name__)


class LoadBalancingPolicy:
    """Abstract class for load balancing policies."""

    def __init__(self) -> None:
        self.ready_replicas: List[str] = []

    def set_ready_replicas(self, ready_replicas: List[str]) -> None:
        raise NotImplementedError

    def select_replica(self, request: fastapi.Request) -> Optional[str]:
        raise NotImplementedError


class RoundRobinPolicy(LoadBalancingPolicy):
    """Round-robin load balancing policy."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.index = 0

    def set_ready_replicas(self, ready_replicas: List[str]) -> None:
        if set(ready_replicas) != set(self.ready_replicas):
            # If the autoscaler keeps scaling up and down the replicas,
            # we need this shuffle to not let the first replica have the
            # most of the load.
            random.shuffle(ready_replicas)
            self.ready_replicas = ready_replicas
            self.index = 0

    def select_replica(self, request: fastapi.Request) -> Optional[str]:
        if not self.ready_replicas:
            return None
        replica_ip = self.ready_replicas[self.index]
        self.index = (self.index + 1) % len(self.ready_replicas)
        request_repr = ('<Request '
                        f'method="{request.method}" '
                        f'url="{request.url}" '
                        f'headers={dict(request.headers)} '
                        f'query_params={dict(request.query_params)}'
                        '>')
        logger.info(f'Selected replica {replica_ip} for request {request_repr}')
        return replica_ip
