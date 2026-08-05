package com.veloceeo.feature.home.utils

import androidx.compose.runtime.Composable

@Composable
expect fun rememberImagePickerLauncher(onImagePicked: (ByteArray) -> Unit): () -> Unit
