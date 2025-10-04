#!/usr/bin/env python3
"""
Geography-Locked Tokens for DRP
Implements location-based token restrictions with GPS attestation
"""

import json
import hashlib
import logging
import math
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocationType(Enum):
    """Types of location restrictions"""
    COUNTRY = "country"
    REGION = "region"
    CITY = "city"
    COORDINATES = "coordinates"
    RADIUS = "radius"
    POLYGON = "polygon"


class AttestationStatus(Enum):
    """Status of location attestation"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class Location:
    """Represents a geographical location"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: Optional[str] = None


@dataclass
class LocationRestriction:
    """Represents a location-based restriction"""
    restriction_id: str
    location_type: LocationType
    allowed_locations: List[Dict[str, Any]]
    restricted_locations: List[Dict[str, Any]]
    radius_meters: Optional[float] = None
    created_at: str = ""
    expires_at: Optional[str] = None


@dataclass
class GPSAttestation:
    """Represents a GPS location attestation"""
    attestation_id: str
    user_address: str
    location: Location
    device_info: Dict[str, Any]
    signature: str
    timestamp: str
    status: AttestationStatus
    validator: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GeographyLockedToken:
    """Represents a geography-locked token"""
    token_id: str
    owner: str
    amount: int
    location_restrictions: List[LocationRestriction]
    attestation_required: bool
    created_at: str
    status: str = "active"


class GPSAttestationService:
    """
    Service for GPS location attestation and validation
    """
    
    def __init__(self, validator_private_key: str):
        """
        Initialize GPS attestation service
        
        Args:
            validator_private_key: Private key for signing attestations
        """
        self.validator_private_key = validator_private_key
        self.attestations: Dict[str, GPSAttestation] = {}
        self.attestation_expiry_hours = 24  # Attestations expire after 24 hours
        
        logger.info("GPS Attestation Service initialized")
    
    def create_attestation(
        self, 
        user_address: str, 
        location: Location, 
        device_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> GPSAttestation:
        """
        Create a GPS location attestation
        
        Args:
            user_address: Address of the user
            location: GPS location data
            device_info: Device information
            metadata: Optional metadata
            
        Returns:
            GPS attestation
        """
        try:
            # Generate attestation ID
            attestation_id = hashlib.sha256(
                f"{user_address}_{location.latitude}_{location.longitude}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16]
            
            # Create attestation data
            attestation_data = {
                "attestation_id": attestation_id,
                "user_address": user_address,
                "location": asdict(location),
                "device_info": device_info,
                "timestamp": datetime.utcnow().isoformat(),
                "validator": "gps_validator_1"
            }
            
            # Sign attestation (simplified - in practice use proper cryptographic signing)
            signature = self._sign_attestation(attestation_data)
            
            attestation = GPSAttestation(
                attestation_id=attestation_id,
                user_address=user_address,
                location=location,
                device_info=device_info,
                signature=signature,
                timestamp=datetime.utcnow().isoformat(),
                status=AttestationStatus.VALID,
                validator="gps_validator_1",
                metadata=metadata
            )
            
            self.attestations[attestation_id] = attestation
            
            logger.info(f"Created GPS attestation {attestation_id} for user {user_address}")
            return attestation
            
        except Exception as e:
            logger.error(f"Error creating GPS attestation: {e}")
            raise
    
    def _sign_attestation(self, attestation_data: Dict[str, Any]) -> str:
        """Sign attestation data"""
        # Simplified signing - in practice use proper cryptographic signing
        data_string = json.dumps(attestation_data, sort_keys=True)
        signature = hashlib.sha256(
            (data_string + self.validator_private_key).encode()
        ).hexdigest()
        return signature
    
    def verify_attestation(self, attestation_id: str) -> bool:
        """
        Verify a GPS attestation
        
        Args:
            attestation_id: Attestation identifier
            
        Returns:
            True if attestation is valid
        """
        try:
            if attestation_id not in self.attestations:
                logger.error(f"Attestation {attestation_id} not found")
                return False
            
            attestation = self.attestations[attestation_id]
            
            # Check if attestation is expired
            attestation_time = datetime.fromisoformat(attestation.timestamp)
            expiry_time = attestation_time + timedelta(hours=self.attestation_expiry_hours)
            
            if datetime.utcnow() > expiry_time:
                attestation.status = AttestationStatus.EXPIRED
                logger.error(f"Attestation {attestation_id} has expired")
                return False
            
            # Verify signature (simplified)
            attestation_data = {
                "attestation_id": attestation.attestation_id,
                "user_address": attestation.user_address,
                "location": asdict(attestation.location),
                "device_info": attestation.device_info,
                "timestamp": attestation.timestamp,
                "validator": attestation.validator
            }
            
            expected_signature = self._sign_attestation(attestation_data)
            is_valid = attestation.signature == expected_signature
            
            if is_valid:
                logger.info(f"GPS attestation {attestation_id} verified successfully")
            else:
                logger.error(f"GPS attestation {attestation_id} verification failed")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying GPS attestation: {e}")
            return False
    
    def get_attestation(self, attestation_id: str) -> Optional[GPSAttestation]:
        """Get attestation by ID"""
        return self.attestations.get(attestation_id)
    
    def revoke_attestation(self, attestation_id: str) -> bool:
        """Revoke an attestation"""
        if attestation_id in self.attestations:
            self.attestations[attestation_id].status = AttestationStatus.REVOKED
            logger.info(f"Attestation {attestation_id} revoked")
            return True
        return False


class GeographyLockedTokenManager:
    """
    Manager for geography-locked tokens with GPS attestation
    """
    
    def __init__(self, attestation_service: GPSAttestationService):
        """
        Initialize geography-locked token manager
        
        Args:
            attestation_service: GPS attestation service
        """
        self.attestation_service = attestation_service
        self.tokens: Dict[str, GeographyLockedToken] = {}
        self.location_restrictions: Dict[str, LocationRestriction] = {}
        
        logger.info("Geography-Locked Token Manager initialized")
    
    def create_location_restriction(
        self,
        restriction_id: str,
        location_type: LocationType,
        allowed_locations: List[Dict[str, Any]],
        restricted_locations: Optional[List[Dict[str, Any]]] = None,
        radius_meters: Optional[float] = None,
        expires_at: Optional[str] = None
    ) -> bool:
        """
        Create a location restriction
        
        Args:
            restriction_id: Unique identifier
            location_type: Type of location restriction
            allowed_locations: List of allowed locations
            restricted_locations: List of restricted locations
            radius_meters: Radius for coordinate-based restrictions
            expires_at: Expiration timestamp
            
        Returns:
            True if restriction created successfully
        """
        try:
            if restriction_id in self.location_restrictions:
                logger.error(f"Location restriction {restriction_id} already exists")
                return False
            
            restriction = LocationRestriction(
                restriction_id=restriction_id,
                location_type=location_type,
                allowed_locations=allowed_locations,
                restricted_locations=restricted_locations or [],
                radius_meters=radius_meters,
                created_at=datetime.utcnow().isoformat(),
                expires_at=expires_at
            )
            
            self.location_restrictions[restriction_id] = restriction
            
            logger.info(f"Created location restriction {restriction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating location restriction: {e}")
            return False
    
    def create_geography_locked_token(
        self,
        token_id: str,
        owner: str,
        amount: int,
        location_restrictions: List[str],  # List of restriction IDs
        attestation_required: bool = True
    ) -> bool:
        """
        Create a geography-locked token
        
        Args:
            token_id: Unique token identifier
            owner: Token owner address
            amount: Token amount
            location_restrictions: List of restriction IDs
            attestation_required: Whether GPS attestation is required
            
        Returns:
            True if token created successfully
        """
        try:
            if token_id in self.tokens:
                logger.error(f"Geography-locked token {token_id} already exists")
                return False
            
            # Validate restrictions exist
            for restriction_id in location_restrictions:
                if restriction_id not in self.location_restrictions:
                    logger.error(f"Location restriction {restriction_id} not found")
                    return False
            
            # Get restriction objects
            restrictions = [self.location_restrictions[rid] for rid in location_restrictions]
            
            token = GeographyLockedToken(
                token_id=token_id,
                owner=owner,
                amount=amount,
                location_restrictions=restrictions,
                attestation_required=attestation_required,
                created_at=datetime.utcnow().isoformat()
            )
            
            self.tokens[token_id] = token
            
            logger.info(f"Created geography-locked token {token_id} for {amount} tokens")
            return True
            
        except Exception as e:
            logger.error(f"Error creating geography-locked token: {e}")
            return False
    
    def check_location_permission(
        self, 
        token_id: str, 
        user_location: Location, 
        attestation_id: Optional[str] = None
    ) -> bool:
        """
        Check if a user can transfer tokens from their current location
        
        Args:
            token_id: Token identifier
            user_location: User's current location
            attestation_id: Optional GPS attestation ID
            
        Returns:
            True if transfer is allowed
        """
        try:
            if token_id not in self.tokens:
                logger.error(f"Token {token_id} not found")
                return False
            
            token = self.tokens[token_id]
            
            # Check if attestation is required
            if token.attestation_required:
                if not attestation_id:
                    logger.error(f"GPS attestation required for token {token_id}")
                    return False
                
                # Verify attestation
                if not self.attestation_service.verify_attestation(attestation_id):
                    logger.error(f"Invalid GPS attestation {attestation_id}")
                    return False
                
                # Get attestation and verify location matches
                attestation = self.attestation_service.get_attestation(attestation_id)
                if attestation and not self._locations_match(attestation.location, user_location):
                    logger.error("Attestation location does not match user location")
                    return False
            
            # Check location restrictions
            for restriction in token.location_restrictions:
                if not self._check_location_restriction(user_location, restriction):
                    logger.error(f"Location restriction {restriction.restriction_id} violated")
                    return False
            
            logger.info(f"Location permission granted for token {token_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking location permission: {e}")
            return False
    
    def _locations_match(self, location1: Location, location2: Location, tolerance_meters: float = 100.0) -> bool:
        """Check if two locations match within tolerance"""
        distance = self._calculate_distance(location1, location2)
        return distance <= tolerance_meters
    
    def _calculate_distance(self, location1: Location, location2: Location) -> float:
        """Calculate distance between two locations in meters"""
        # Haversine formula
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(location1.latitude)
        lat2_rad = math.radians(location2.latitude)
        delta_lat = math.radians(location2.latitude - location1.latitude)
        delta_lon = math.radians(location2.longitude - location1.longitude)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _check_location_restriction(self, user_location: Location, restriction: LocationRestriction) -> bool:
        """Check if user location satisfies a restriction"""
        try:
            if restriction.location_type == LocationType.COUNTRY:
                # Check if user is in allowed countries
                user_country = self._get_country_from_coordinates(user_location.latitude, user_location.longitude)
                allowed_countries = [loc.get("country") for loc in restriction.allowed_locations]
                return user_country in allowed_countries
            
            elif restriction.location_type == LocationType.COORDINATES:
                # Check if user is within allowed coordinate areas
                for allowed_loc in restriction.allowed_locations:
                    allowed_location = Location(
                        latitude=allowed_loc["latitude"],
                        longitude=allowed_loc["longitude"]
                    )
                    if restriction.radius_meters:
                        distance = self._calculate_distance(user_location, allowed_location)
                        if distance <= restriction.radius_meters:
                            return True
                    else:
                        # Exact coordinate match
                        if (abs(user_location.latitude - allowed_location.latitude) < 0.0001 and
                            abs(user_location.longitude - allowed_location.longitude) < 0.0001):
                            return True
            
            elif restriction.location_type == LocationType.POLYGON:
                # Check if user is within polygon
                for polygon in restriction.allowed_locations:
                    if self._point_in_polygon(user_location, polygon["coordinates"]):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking location restriction: {e}")
            return False
    
    def _get_country_from_coordinates(self, latitude: float, longitude: float) -> str:
        """Get country from coordinates (simplified implementation)"""
        # This is a simplified implementation
        # In practice, use a proper geocoding service
        if 24.0 <= latitude <= 49.0 and -125.0 <= longitude <= -66.0:
            return "US"
        elif 35.0 <= latitude <= 71.0 and -10.0 <= longitude <= 40.0:
            return "EU"
        elif 3.0 <= latitude <= 35.0 and 68.0 <= longitude <= 97.0:
            return "IN"
        else:
            return "OTHER"
    
    def _point_in_polygon(self, point: Location, polygon: List[List[float]]) -> bool:
        """Check if point is inside polygon using ray casting algorithm"""
        x, y = point.longitude, point.latitude
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def transfer_token(
        self, 
        token_id: str, 
        from_address: str, 
        to_address: str, 
        amount: int,
        user_location: Location,
        attestation_id: Optional[str] = None
    ) -> bool:
        """
        Transfer geography-locked token with location verification
        
        Args:
            token_id: Token identifier
            from_address: Sender address
            to_address: Recipient address
            amount: Amount to transfer
            user_location: User's current location
            attestation_id: Optional GPS attestation ID
            
        Returns:
            True if transfer successful
        """
        try:
            if token_id not in self.tokens:
                logger.error(f"Token {token_id} not found")
                return False
            
            token = self.tokens[token_id]
            
            # Check ownership
            if token.owner != from_address:
                logger.error(f"User {from_address} does not own token {token_id}")
                return False
            
            # Check amount
            if amount > token.amount:
                logger.error(f"Insufficient token balance: {amount} > {token.amount}")
                return False
            
            # Check location permission
            if not self.check_location_permission(token_id, user_location, attestation_id):
                logger.error(f"Location permission denied for token {token_id}")
                return False
            
            # Perform transfer
            token.amount -= amount
            if token.amount == 0:
                token.status = "transferred"
            
            logger.info(f"Transferred {amount} tokens from {from_address} to {to_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error transferring token: {e}")
            return False
    
    def get_token_info(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get token information"""
        if token_id not in self.tokens:
            return None
        
        token = self.tokens[token_id]
        return asdict(token)


def main():
    """Command line interface for geography-locked tokens"""
    parser = argparse.ArgumentParser(description="DRP Geography-Locked Tokens Demo")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    
    args = parser.parse_args()
    
    try:
        # Initialize services
        attestation_service = GPSAttestationService("validator_private_key_123")
        token_manager = GeographyLockedTokenManager(attestation_service)
        
        print(f"🌍 Geography-Locked Tokens System Initialized")
        
        if args.demo:
            print(f"\n🔒 Geography-Locked Tokens Demo")
            print(f"=" * 50)
            
            # Create location restrictions
            print(f"Creating location restrictions...")
            
            # US-only restriction
            token_manager.create_location_restriction(
                "us_only",
                LocationType.COUNTRY,
                [{"country": "US"}]
            )
            
            # Specific coordinates restriction
            token_manager.create_location_restriction(
                "sf_bay_area",
                LocationType.COORDINATES,
                [{"latitude": 37.7749, "longitude": -122.4194}],  # San Francisco
                radius_meters=50000  # 50km radius
            )
            
            # Create geography-locked token
            print(f"Creating geography-locked token...")
            token_manager.create_geography_locked_token(
                "geo_token_1",
                "0xuser1",
                1000000,
                ["us_only"],
                attestation_required=True
            )
            
            # Create GPS attestation
            print(f"Creating GPS attestation...")
            user_location = Location(
                latitude=37.7749,
                longitude=-122.4194,
                accuracy=10.0,
                timestamp=datetime.utcnow().isoformat()
            )
            
            device_info = {
                "device_id": "device_123",
                "os": "iOS 15.0",
                "app_version": "1.0.0"
            }
            
            attestation = attestation_service.create_attestation(
                "0xuser1",
                user_location,
                device_info
            )
            
            print(f"   Attestation ID: {attestation.attestation_id}")
            print(f"   Location: {user_location.latitude}, {user_location.longitude}")
            
            # Test location permission
            print(f"\n🔍 Testing location permissions...")
            
            # Test with valid location and attestation
            permission = token_manager.check_location_permission(
                "geo_token_1",
                user_location,
                attestation.attestation_id
            )
            print(f"   US location with attestation: {'✅ Allowed' if permission else '❌ Denied'}")
            
            # Test with invalid location (simulate EU location)
            eu_location = Location(latitude=52.5200, longitude=13.4050)  # Berlin
            permission = token_manager.check_location_permission(
                "geo_token_1",
                eu_location,
                attestation.attestation_id
            )
            print(f"   EU location with attestation: {'✅ Allowed' if permission else '❌ Denied'}")
            
            # Test token transfer
            print(f"\n💸 Testing token transfer...")
            transfer_success = token_manager.transfer_token(
                "geo_token_1",
                "0xuser1",
                "0xuser2",
                100000,
                user_location,
                attestation.attestation_id
            )
            print(f"   Token transfer: {'✅ Success' if transfer_success else '❌ Failed'}")
            
            # Show token info
            token_info = token_manager.get_token_info("geo_token_1")
            if token_info:
                print(f"\n📊 Token Information:")
                print(f"   Token ID: {token_info['token_id']}")
                print(f"   Owner: {token_info['owner']}")
                print(f"   Amount: {token_info['amount']}")
                print(f"   Status: {token_info['status']}")
                print(f"   Attestation Required: {token_info['attestation_required']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())


