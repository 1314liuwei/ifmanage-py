import os


def makedir(path, user=None, group=None):
    if os.path.exists(path):
        return
    os.makedirs(path, mode=0o755)
    chown(path, user, group)


def chown(path, user, group):
    """ change file/directory owner """
    from pwd import getpwnam
    from grp import getgrnam

    if user is None or group is None:
        return False

    # path may also be an open file descriptor
    if not isinstance(path, int) and not os.path.exists(path):
        return False

    uid = getpwnam(user).pw_uid
    gid = getgrnam(group).gr_gid
    os.chown(path, uid, gid)
    return True

def chmod(path, bitmask):
    # path may also be an open file descriptor
    if not isinstance(path, int) and not os.path.exists(path):
        return
    if bitmask is None:
        return
    os.chmod(path, bitmask)