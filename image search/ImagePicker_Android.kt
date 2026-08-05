package com.veloceeo.feature.home.utils

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

@Composable
actual fun rememberImagePickerLauncher(onImagePicked: (ByteArray) -> Unit): () -> Unit {
    val context = LocalContext.current

    val launcher =
        rememberLauncherForActivityResult(
            contract = ActivityResultContracts.GetContent(),
        ) { uri: Uri? ->
            if (uri != null) {
                try {
                    val inputStream = context.contentResolver.openInputStream(uri)
                    val bytes = inputStream?.readBytes()
                    inputStream?.close()
                    if (bytes != null && bytes.isNotEmpty()) {
                        onImagePicked(bytes)
                    }
                } catch (_: Exception) {
                    // Handle image read error
                }
            }
        }

    return {
        launcher.launch("image/*")
    }
}
