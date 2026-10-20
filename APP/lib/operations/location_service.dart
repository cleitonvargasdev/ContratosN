import 'dart:async';

import 'package:geolocator/geolocator.dart';

class LocationFailure implements Exception {
  const LocationFailure(this.message);
  final String message;
}

class OperationLocation {
  Future<Map<String, Object?>> capture() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw const LocationFailure(
        'Ligue a localização do aparelho para continuar.',
      );
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission != LocationPermission.whileInUse &&
        permission != LocationPermission.always) {
      throw const LocationFailure(
        'Permita o acesso à localização nas configurações do aparelho.',
      );
    }
    final started = DateTime.now().toUtc();
    try {
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 30),
        ),
      );
      return {
        'status': 'captured',
        'latitude': position.latitude,
        'longitude': position.longitude,
        'accuracy': position.accuracy,
        'attempted_at': started.toIso8601String(),
        'captured_at': position.timestamp.toUtc().toIso8601String(),
      };
    } on TimeoutException {
      // Disabled GPS or revoked permission must never become a timeout bypass.
      final stillEnabled = await Geolocator.isLocationServiceEnabled();
      final currentPermission = await Geolocator.checkPermission();
      if (!stillEnabled ||
          (currentPermission != LocationPermission.whileInUse &&
              currentPermission != LocationPermission.always)) {
        throw const LocationFailure(
          'Mantenha a localização ligada e autorizada.',
        );
      }
      return {
        'status': 'timeout',
        'latitude': null,
        'longitude': null,
        'attempted_at': started.toIso8601String(),
      };
    }
  }
}
