// Modern Premium Search Bar UI Redesign in HomeScreen.kt

OutlinedTextField(
    value = text,
    onValueChange = { value ->
        text = value
        viewModel.onSearchQueryChanged(value)
    },
    singleLine = true,
    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
    keyboardActions = KeyboardActions(onSearch = {
        viewModel.onSearchQueryChanged(text)
    }),
    modifier = Modifier
        .weight(1f)
        .height(52.dp)
        .shadow(2.dp, RoundedCornerShape(26.dp)),
    shape = RoundedCornerShape(26.dp),
    placeholder = {
        Text(
            text = "Search products, stores...",
            color = Color.Gray,
            fontSize = 14.sp,
        )
    },
    leadingIcon = {
        Icon(
            imageVector = Icons.Default.Search,
            contentDescription = "Search",
            tint = Color(0xFFA7533E),
            modifier = Modifier.size(20.dp).clickable { viewModel.onSearchQueryChanged(text) },
        )
    },
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
    },
    colors = OutlinedTextFieldDefaults.colors(
        focusedContainerColor = Color.White,
        unfocusedContainerColor = Color.White,
        disabledContainerColor = Color.White,
        focusedBorderColor = Color(0xFFA7533E).copy(alpha = 0.5f),
        unfocusedBorderColor = Color.Transparent,
    ),
)
