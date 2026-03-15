from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BrokerPosition:
    symbol: str
    quantity: float
    cost_basis_per_share: float | None
    asset_name: str
    asset_type: str
    currency: str


@dataclass
class BrokerAccount:
    external_id: str
    name: str
    positions: list[BrokerPosition]


class BrokerAdapter(ABC):
    @abstractmethod
    def authenticate(self, credentials: dict) -> bool:
        ...

    @abstractmethod
    def fetch_accounts(self) -> list[BrokerAccount]:
        ...

    @abstractmethod
    def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        ...


class StubBrokerAdapter(BrokerAdapter):
    """Stub implementation for development. Returns sample data."""

    def authenticate(self, credentials: dict) -> bool:
        return True

    def fetch_accounts(self) -> list[BrokerAccount]:
        return [
            BrokerAccount(
                external_id="stub-001",
                name="Stub Brokerage Account",
                positions=self.fetch_positions("stub-001"),
            )
        ]

    def fetch_positions(self, account_id: str) -> list[BrokerPosition]:
        return [
            BrokerPosition(symbol="AAPL", quantity=50, cost_basis_per_share=150.0, asset_name="Apple Inc.", asset_type="equity", currency="USD"),
            BrokerPosition(symbol="MSFT", quantity=30, cost_basis_per_share=280.0, asset_name="Microsoft Corp.", asset_type="equity", currency="USD"),
            BrokerPosition(symbol="GOOGL", quantity=20, cost_basis_per_share=130.0, asset_name="Alphabet Inc.", asset_type="equity", currency="USD"),
        ]
