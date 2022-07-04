import storage

#This disables concurrent write protection (This is not exactly safe...and should only be used during development purposes)
storage.remount(mount_path="/",disable_concurrent_write_protection=True)
print("Concurrent write protection disabled2")
