"""
SGP4 konum hesaplama motoru.
Gereksinimler: 8.1, 8.2, 8.3, 8.4
"""

import math
from datetime import datetime, timezone
from sgp4.api import Satrec, jday


class PropagationError(Exception):
    """SGP4 propagasyon hatası."""
    pass


class CoordinateError(Exception):
    """ECI → Geodetik dönüşüm hatası."""
    pass


# WGS-84 sabitleri
_WGS84_A = 6378.137        # km — büyük yarı eksen
_WGS84_F = 1 / 298.257223563
_WGS84_B = _WGS84_A * (1 - _WGS84_F)
_WGS84_E2 = 1 - (_WGS84_B / _WGS84_A) ** 2


class SGP4Engine:
    """sgp4 kütüphanesi ile TLE tabanlı uydu konum hesaplama motoru."""

    # ------------------------------------------------------------------ #
    # Yardımcı: TLE doğrulama ve Satrec oluşturma                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_satrec(tle_line1: str, tle_line2: str) -> Satrec:
        """TLE satırlarından Satrec nesnesi oluşturur; geçersizse ValueError fırlatır."""
        if not isinstance(tle_line1, str) or not isinstance(tle_line2, str):
            raise ValueError("TLE satırları string olmalıdır.")
        l1 = tle_line1.strip()
        l2 = tle_line2.strip()
        if len(l1) < 69 or len(l2) < 69:
            raise ValueError(f"TLE satır uzunluğu geçersiz: line1={len(l1)}, line2={len(l2)}")
        if not l1.startswith("1 ") and not l1.startswith("1"):
            raise ValueError("TLE satır 1 '1' ile başlamalıdır.")
        if not l2.startswith("2 ") and not l2.startswith("2"):
            raise ValueError("TLE satır 2 '2' ile başlamalıdır.")
        sat = Satrec.twoline2rv(l1, l2)
        # sgp4 kütüphanesi hata kodunu error alanında saklar
        if sat.error != 0:
            raise ValueError(f"TLE ayrıştırma hatası (error={sat.error}): {l1[:30]}...")
        return sat

    # ------------------------------------------------------------------ #
    # propagate                                                            #
    # ------------------------------------------------------------------ #

    def propagate(self, tle_line1: str, tle_line2: str, dt: datetime) -> dict:
        """
        TLE ve zaman damgasından ECI koordinatları + hız vektörü hesaplar.

        Returns:
            {
                "eci": {"x": float, "y": float, "z": float},      # km
                "velocity": {"vx": float, "vy": float, "vz": float}  # km/s
            }

        Raises:
            ValueError: Geçersiz TLE formatı.
            PropagationError: SGP4 propagasyon hatası.
        """
        sat = self._build_satrec(tle_line1, tle_line2)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_utc = dt.astimezone(timezone.utc)

        jd, fr = jday(
            dt_utc.year,
            dt_utc.month,
            dt_utc.day,
            dt_utc.hour,
            dt_utc.minute,
            dt_utc.second + dt_utc.microsecond / 1e6,
        )

        e, r, v = sat.sgp4(jd, fr)
        if e != 0:
            raise PropagationError(
                f"SGP4 propagasyon hatası (error={e}). "
                "Uydu yörüngeden çıkmış veya TLE süresi dolmuş olabilir."
            )

        return {
            "eci": {"x": r[0], "y": r[1], "z": r[2]},
            "velocity": {"vx": v[0], "vy": v[1], "vz": v[2]},
        }

    # ------------------------------------------------------------------ #
    # eci_to_geodetic                                                      #
    # ------------------------------------------------------------------ #

    def eci_to_geodetic(self, x: float, y: float, z: float, dt: datetime) -> dict:
        """
        ECI koordinatlarını geodetik koordinatlara dönüştürür.

        Returns:
            {"lat": float, "lon": float, "alt_km": float}

        Raises:
            CoordinateError: Dönüşüm sırasında hata oluşursa.
        """
        try:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)

            # Greenwich Açısal Saati (GMST) — basit yaklaşım
            gmst = self._gmst(dt_utc)

            # ECI → ECEF
            cos_g = math.cos(gmst)
            sin_g = math.sin(gmst)
            x_ecef = x * cos_g + y * sin_g
            y_ecef = -x * sin_g + y * cos_g
            z_ecef = z

            # ECEF → Geodetik (Bowring iterasyonu)
            lon_rad = math.atan2(y_ecef, x_ecef)
            p = math.sqrt(x_ecef ** 2 + y_ecef ** 2)

            # Başlangıç tahmini
            lat_rad = math.atan2(z_ecef, p * (1 - _WGS84_E2))
            for _ in range(10):
                sin_lat = math.sin(lat_rad)
                N = _WGS84_A / math.sqrt(1 - _WGS84_E2 * sin_lat ** 2)
                lat_new = math.atan2(z_ecef + _WGS84_E2 * N * sin_lat, p)
                if abs(lat_new - lat_rad) < 1e-12:
                    break
                lat_rad = lat_new
            lat_rad = lat_new

            sin_lat = math.sin(lat_rad)
            cos_lat = math.cos(lat_rad)
            N = _WGS84_A / math.sqrt(1 - _WGS84_E2 * sin_lat ** 2)

            if abs(cos_lat) > 1e-10:
                alt_km = p / cos_lat - N
            else:
                alt_km = abs(z_ecef) / abs(sin_lat) - N * (1 - _WGS84_E2)

            lat_deg = math.degrees(lat_rad)
            lon_deg = math.degrees(lon_rad)

            # Boylam [-180, 180] aralığına normalize et
            lon_deg = (lon_deg + 180) % 360 - 180

            return {"lat": lat_deg, "lon": lon_deg, "alt_km": alt_km}

        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            raise CoordinateError(f"ECI → Geodetik dönüşüm hatası: {exc}") from exc

    # ------------------------------------------------------------------ #
    # orbital_elements                                                     #
    # ------------------------------------------------------------------ #

    def orbital_elements(self, tle_line1: str, tle_line2: str) -> dict:
        """
        TLE'den yörünge parametrelerini hesaplar.

        Returns:
            {
                "perigee_km": float,
                "apogee_km": float,
                "period_min": float,
                "inclination_deg": float,
                "orbit_type": str   # "GEO" | "LEO" | "MEO"
            }

        Raises:
            ValueError: Geçersiz TLE formatı.
        """
        sat = self._build_satrec(tle_line1, tle_line2)

        # sgp4 Satrec alanları (rad/min cinsinden)
        # no_kozai: ortalama hareket (rad/min)
        # ecco: dışmerkezlik
        # inclo: inklinasyon (rad)
        mu = 398600.4418  # km³/s²

        # Ortalama hareket rad/min → rad/s
        n_rad_per_s = sat.no_kozai / 60.0

        # Yarı büyük eksen (km)
        if n_rad_per_s <= 0:
            raise ValueError("Geçersiz ortalama hareket değeri.")
        a_km = (mu / (n_rad_per_s ** 2)) ** (1 / 3)

        ecc = sat.ecco
        re = _WGS84_A  # Dünya yarıçapı (km)

        perigee_km = a_km * (1 - ecc) - re
        apogee_km = a_km * (1 + ecc) - re
        period_min = 2 * math.pi / sat.no_kozai  # no_kozai rad/min
        inclination_deg = math.degrees(sat.inclo)

        # Yörünge tipi — ortalama irtifaya göre
        mean_alt_km = (perigee_km + apogee_km) / 2
        if mean_alt_km > 35000:
            orbit_type = "GEO"
        elif mean_alt_km < 2000:
            orbit_type = "LEO"
        else:
            orbit_type = "MEO"

        return {
            "perigee_km": perigee_km,
            "apogee_km": apogee_km,
            "period_min": period_min,
            "inclination_deg": inclination_deg,
            "orbit_type": orbit_type,
        }

    # ------------------------------------------------------------------ #
    # Yardımcı: GMST hesabı                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _gmst(dt_utc: datetime) -> float:
        """
        Verilen UTC zamanı için Greenwich Ortalama Yıldız Saatini (GMST) radyan cinsinden döndürür.
        IAU 1982 formülü kullanılır.
        """
        # Julian Date
        jd, fr = jday(
            dt_utc.year,
            dt_utc.month,
            dt_utc.day,
            dt_utc.hour,
            dt_utc.minute,
            dt_utc.second + dt_utc.microsecond / 1e6,
        )
        jd_total = jd + fr
        # J2000.0 epoch: JD 2451545.0
        T = (jd_total - 2451545.0) / 36525.0
        # GMST saniye cinsinden (IAU 1982)
        gmst_sec = (
            67310.54841
            + (876600 * 3600 + 8640184.812866) * T
            + 0.093104 * T ** 2
            - 6.2e-6 * T ** 3
        )
        gmst_rad = math.radians(gmst_sec / 240.0) % (2 * math.pi)
        return gmst_rad
