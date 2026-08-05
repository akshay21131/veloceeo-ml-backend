package com.veloceeo.feature.home.utils

import androidx.compose.runtime.Composable

@Composable
actual fun rememberImagePickerLauncher(onImagePicked: (ByteArray) -> Unit): () -> Unit = {}
