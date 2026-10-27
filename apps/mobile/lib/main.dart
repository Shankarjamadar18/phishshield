import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// Android emulator reaches the host machine at 10.0.2.2.
const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

void main() => runApp(const PhishShieldApp());

class PhishShieldApp extends StatelessWidget {
  const PhishShieldApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'PhishShield',
        theme: ThemeData(colorSchemeSeed: Colors.teal, brightness: Brightness.dark, useMaterial3: true),
        home: const HealthScreen(),
      );
}

class HealthScreen extends StatefulWidget {
  const HealthScreen({super.key});
  @override
  State<HealthScreen> createState() => _HealthScreenState();
}

class _HealthScreenState extends State<HealthScreen> {
  String _status = 'Checking backend…';

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    try {
      final r = await http.get(Uri.parse('$apiUrl/health'));
      final body = jsonDecode(r.body) as Map<String, dynamic>;
      setState(() => _status = 'API ${body['status']} · database ${body['database']}');
    } catch (e) {
      setState(() => _status = 'Backend unreachable at $apiUrl');
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('PhishShield')),
        body: Center(child: Text(_status)),
        floatingActionButton: FloatingActionButton(onPressed: _check, child: const Icon(Icons.refresh)),
      );
}
