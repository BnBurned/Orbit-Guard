"""
Paylaşılan bağımlılıklar — OrbitGuard
Router'lar tarafından FastAPI dependency injection ile kullanılır.
"""

from celestrak_client import CelesTrakClient

# Tüm router'lar tarafından paylaşılan singleton CelesTrakClient örneği
celestrak_client = CelesTrakClient()
