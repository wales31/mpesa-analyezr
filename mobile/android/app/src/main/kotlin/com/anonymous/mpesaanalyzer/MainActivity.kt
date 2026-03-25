package com.anonymous.mpesaanalyzer

import android.provider.Telephony
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object {
        private const val CHANNEL = "mpesa_analyzer/sms_reader"
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                if (call.method == "readRecentMpesaSms") {
                    val limit = call.argument<Int>("limit") ?: 80
                    result.success(readRecentMpesaSms(limit))
                } else {
                    result.notImplemented()
                }
            }
    }

    private fun readRecentMpesaSms(limit: Int): List<Map<String, Any?>> {
        val items = mutableListOf<Map<String, Any?>>()
        val projection = arrayOf(
            Telephony.Sms._ID,
            Telephony.Sms.ADDRESS,
            Telephony.Sms.BODY,
            Telephony.Sms.DATE
        )

        val cursor = contentResolver.query(
            Telephony.Sms.Inbox.CONTENT_URI,
            projection,
            null,
            null,
            "${Telephony.Sms.DATE} DESC"
        )

        cursor?.use {
            val idIndex = it.getColumnIndexOrThrow(Telephony.Sms._ID)
            val addressIndex = it.getColumnIndexOrThrow(Telephony.Sms.ADDRESS)
            val bodyIndex = it.getColumnIndexOrThrow(Telephony.Sms.BODY)
            val dateIndex = it.getColumnIndexOrThrow(Telephony.Sms.DATE)

            while (it.moveToNext() && items.size < limit) {
                val address = it.getString(addressIndex) ?: ""
                val body = it.getString(bodyIndex) ?: ""
                if (!isMpesaMessage(address, body)) {
                    continue
                }

                items.add(
                    mapOf(
                        "id" to it.getLong(idIndex).toString(),
                        "address" to address,
                        "body" to body,
                        "date" to it.getLong(dateIndex)
                    )
                )
            }
        }

        return items
    }

    private fun isMpesaMessage(address: String, body: String): Boolean {
        val normalizedAddress = address.uppercase()
        val normalizedBody = body.uppercase()
        return normalizedAddress.contains("MPESA") ||
            normalizedBody.contains("MPESA") ||
            normalizedBody.contains("M-PESA")
    }
}
