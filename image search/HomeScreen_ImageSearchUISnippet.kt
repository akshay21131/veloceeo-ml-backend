// Modern Premium Search Bar UI Redesign Snippet for Image Search in HomeScreen.kt

val launchImagePicker = rememberImagePickerLauncher { imageBytes ->
    viewModel.onImageSelected(imageBytes)
}

// Inside OutlinedTextField trailingIcon:
trailingIcon = {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.padding(end = 6.dp),
    ) {
        Box(
            modifier = Modifier
                .size(34.dp)
                .clip(RoundedCornerShape(17.dp))
                .clickable { launchImagePicker() },
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Default.CameraAlt,
                contentDescription = "Image Search",
                tint = Color(0xFF4A4A4A),
                modifier = Modifier.size(20.dp),
            )
        }
        Spacer(modifier = Modifier.width(2.dp))
        Box(
            modifier = Modifier
                .size(34.dp)
                .clip(RoundedCornerShape(17.dp))
                .clickable { launchVoiceSearch() },
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Default.Mic,
                contentDescription = "Voice Search",
                tint = Color(0xFF4A4A4A),
                modifier = Modifier.size(20.dp),
            )
        }
    }
}
