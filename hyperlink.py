def hyperlink(url, label=None, msg=None, deployed=False):
    """
    Create a string that is displayable as a hyperlink in Python console or GUI.
    
    Parameters
    ----------
    url : str
        URL of the webpage or Python command.
    label : str, optional
        Text label of the hyperlink. Defaults to url.
    msg : str, optional
        If provided, all instances of label in msg will be replaced by the hyperlink.
    deployed : bool, optional
        If True, disables hyperlink formatting (simulates MATLAB deployed behavior).
    
    Returns
    -------
    str
        The string with hyperlink formatting or plain text if deployed.
    """
    if label is None:
        label = url

    is_webpage = url.lower().startswith("http")

    if msg is not None:
        # Replace all occurrences of label in msg with hyperlink
        return msg.replace(label, hyperlink(url, label, deployed=deployed))

    if not deployed:
        # Interactive session
        if is_webpage:
            # HTML-style hyperlink for console or GUI
            return f'<a href="{url}">{label}</a>'
        else:
            # Python command or local reference
            return f'<a href="{url}">{label}</a>'
    else:
        # Deployed / plain-text mode
        if is_webpage and label != url:
            return f"{label} ({url})"
        elif is_webpage:
            return url
        else:
            return label
