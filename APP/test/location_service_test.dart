import 'dart:async';

import 'package:cobrador/operations/location_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';

class FakeGps extends GeolocatorPlatform {
  bool enabled = true;
  bool disableDuringAttempt = false;
  bool timeout = true;
  LocationPermission permission = LocationPermission.whileInUse;
  int attempts = 0;
  LocationSettings? settings;
  @override
  Future<bool> isLocationServiceEnabled() async => enabled;
  @override
  Future<LocationPermission> checkPermission() async => permission;
  @override
  Future<LocationPermission> requestPermission() async => permission;
  @override
  Future<Position> getCurrentPosition({
    LocationSettings? locationSettings,
  }) async {
    attempts++;
    settings = locationSettings;
    if (disableDuringAttempt) enabled = false;
    if (timeout) throw TimeoutException('No fix');
    return Position(
      longitude: -54.5,
      latitude: -20.4,
      timestamp: DateTime.now(),
      accuracy: 8,
      altitude: 0,
      altitudeAccuracy: 0,
      heading: 0,
      headingAccuracy: 0,
      speed: 0,
      speedAccuracy: 0,
    );
  }
}

void main() {
  late FakeGps gps;
  late GeolocatorPlatform original;
  setUp(() {
    original = GeolocatorPlatform.instance;
    gps = FakeGps();
    GeolocatorPlatform.instance = gps;
  });
  tearDown(() => GeolocatorPlatform.instance = original);

  test('timeout de 30 segundos libera sem inventar coordenadas', () async {
    final result = await OperationLocation().capture();
    expect(gps.settings!.timeLimit, const Duration(seconds: 30));
    expect(result['status'], 'timeout');
    expect(result['latitude'], isNull);
    expect(result['longitude'], isNull);
  });
  test('GPS desligado impede confirmação', () async {
    gps.enabled = false;
    await expectLater(
      OperationLocation().capture(),
      throwsA(isA<LocationFailure>()),
    );
    expect(gps.attempts, 0);
  });
  test('permissão negada não usa exceção de timeout', () async {
    gps.permission = LocationPermission.deniedForever;
    await expectLater(
      OperationLocation().capture(),
      throwsA(isA<LocationFailure>()),
    );
    expect(gps.attempts, 0);
  });
  test('desligar GPS durante tentativa não libera confirmação', () async {
    gps.disableDuringAttempt = true;
    await expectLater(
      OperationLocation().capture(),
      throwsA(isA<LocationFailure>()),
    );
  });
  test('posição obtida acompanha a operação', () async {
    gps.timeout = false;
    final result = await OperationLocation().capture();
    expect(result['status'], 'captured');
    expect(result['latitude'], -20.4);
    expect(result['accuracy'], 8);
  });
}
