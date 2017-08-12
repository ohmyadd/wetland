import os
import re
import time
from wetland import config
from wetland.log import loggers

from paramiko import ServerInterface, SFTPServerInterface, SFTPServer, \
                     SFTPAttributes, SFTPHandle, SFTP_OK, AUTH_SUCCESSFUL,\
                     OPEN_SUCCEEDED


class remote_sftp_handle(SFTPHandle):
    def __init__(self, file_name, logger, remote_file, save_file):
        self.remote_file = remote_file
        self.file_name = file_name
        self.save_file = save_file
        self.logger = logger

    def close(self):
        self.logger.info("close filename:%s" % self.file_name)
        self.remote_file.close()
        if self.save_file:
            self.save_file.close()

    def read(self, offset, length):
        self.logger.info("read offset:%d length:%d filename:%s" % (
                                   offset, length, self.file_name))
        if not self.remote_file.readable():
            return SFTP_OP_UNSUPPORTED

        try:
            self.remote_file.seek(offset)
            data = self.remote_file.read(length)
            return data
        except IOError as e:
            self.logger.debug("read error filename:%s %s" % self.filename, e)
            return SFTPServer.convert_errno(e.errno)

    def write(self, offset, data):
        self.logger.info("write offset:%d length:%d filename:%s" % (
                                   offset, len(data), self.file_name))
        if not self.remote_file.writable():
            return SFTP_OP_UNSUPPORTED

        try:
            self.remote_file.seek(offset)
            self.remote_file.write(data)
            self.remote_file.flush()

            self.save_file.seek(offset)
            self.save_file.write(data)
            self.save_file.flush()
        except IOError as e:
            self.logger.debug("write error filename:%s %s" % self.filename, e)
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def stat(self):
        self.logger.info("stat filename:%s" % self.file_name)
        try:
            return self.remote_file.stat()
        except IOError as e:
            self.logger.debug("stat error filename:%s %s" % self.filename, e)
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def chattr(self, attr):
        # python doesn't have equivalents to fchown or fchmod, so we have to
        # use the stored filename
        try:
            if attr._flags & attr.FLAG_PERMISSIONS:
                self.remote_file.chmod(path, attr.st_mode)
                self.logger.info("chmod mod:%o filename:%s" % (attr.st_mode,
                                                               self.file_name))

            if attr._flags & attr.FLAG_UIDGID:
                self.remote_file.chown(path, attr.st_uid, attr.st_gid)
                self.logger.info("chown uid:%d gid:%d filename:%s" % (
                                     attr.st_uid, attr.st_gid, self.file_name))

            if attr._flags & attr.FLAG_AMTIME:
                self.remote_file.utime(path,
                                         (attr.st_atime, attr.st_mtime))
                self.logger.info("utime atime:%d mtime:%d filename:%s" % (
                                 attr.st_atime, attr.st_mtime, self.file_name))

            if attr._flags & attr.FLAG_SIZE:
                self.remote_file.truncate(path, attr.st_size)
                self.logger.info("truncate size:%d filename:%s"%(attr.st_size,
                                                               self.file_name))

        except IOError as e:
            self.logger.debug("chattr error filename:%s %s"%(self.filename, e))
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK


class sftp_server (SFTPServerInterface):
    # assume current folder is a fine root
    # (the tests always create and eventualy delete a subfolder, so there shouldn't be any mess)
    def __init__(self, ssh_server):
        self.ssh_server = ssh_server
        self.docker_client = ssh_server.docker_trans.open_sftp_client()
        self.root = self.docker_client.getcwd()
        self.cfg = config.cfg
        self.logger = loggers().get("sftp", self.ssh_server.hacker_ip)

    def canonicalize(self, path):
        return self.docker_client.normalize(path)

    def list_folder(self, path):
        self.logger.info("list folder path:%s" % path)
        try:
            return self.docker_client.listdir_attr(path)
        except IOError as e:
            self.logger.debug("list folder error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)

    def stat(self, path):

        self.logger.info("get file status path:%s" % path)
        try:
            return self.docker_client.stat(path)
        except IOError as e:
            self.logger.debug("get file status error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)

    def lstat(self, path):

        self.logger.info("get file lstatus path:%s" % path)
        try:
            return self.docker_client.lstat(path)
        except IOError as e:
            self.logger.debug("get file lstatus error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)

    def open(self, path, flags, attr):

        binary_flag = getattr(os, 'O_BINARY',  0)
        flags |= binary_flag
        save_file = None

        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            self.chattr(path, attr)

        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                fstr = 'ab'
            else:
                fstr = 'wb'
            save_dir = self.cfg.get("files", "sftp")
            file_name = [self.ssh_server.hacker_ip]
            file_name.append(time.strftime('%Y%m%d%H%M%S'))
            file_name.append(re.sub('[^A-Za-z0-0]', '-', path))
            file_name = '_'.join(file_name)
            save_path = os.path.join(save_dir, file_name)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_file = open(save_path, fstr)

        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                fstr = 'a+b'
            else:
                fstr = 'r+b'
        else:
            # O_RDONLY (== 0)
            fstr = 'rb'

        self.logger.info("open file mode:%s path:%s" % (fstr, path))
        try:
            remote_file = self.docker_client.file(path, fstr)
        except IOError as e:
            self.logger.debug("get file lstatus error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)

        fobj = remote_sftp_handle(path, self.logger, remote_file, save_file)
        return fobj

    def remove(self, path):
        self.logger.info("remove file path:%s" % path)
        try:
            self.docker_client.remove(path)
        except IOError as e:
            self.logger.debug("remove error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def rename(self, oldpath, newpath):
        self.logger.info("rename file from:%s to:%s" % (oldpath, newpath))
        try:
            self.docker_client.rename(oldpath, newpath)
        except IOError as e:
            self.logger.debug("rename error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def mkdir(self, path, attr):
        self.logger.info("mkdir path:%s" % path)
        try:
            self.docker_client.mkdir(path)
        except IOError as e:
            self.logger.debug("mkdir error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def rmdir(self, path):
        self.logger.info("rmdir path:%s" % path)
        try:
            self.docker_client.rmdir(path)
        except IOError as e:
            self.logger.debug("rmdir error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def chattr(self, path, attr):
        try:
            if attr._flags & attr.FLAG_PERMISSIONS:
                self.docker_client.chmod(path, attr.st_mode)
                self.logger.info("chmod mod:%o path:%s" % (attr.st_mode, path))

            if attr._flags & attr.FLAG_UIDGID:
                self.docker_client.chown(path, attr.st_uid, attr.st_gid)
                self.logger.info("chown uid:%d gid:%d path:%s" % (
                                              attr.st_uid, attr.st_gid, path))

            if attr._flags & attr.FLAG_AMTIME:
                self.docker_client.utime(path,
                                         (attr.st_atime, attr.st_mtime))
                self.logger.info("utime atime:%d stime:%d path:%s" % (
                                          attr.st_atime, attr.st_mtime, path))

            if attr._flags & attr.FLAG_SIZE:
                self.docker_client.truncate(path, attr.st_size)
                self.logger.info("truncate size:%d path:%s" % (attr.st_size,
                                                               path))

        except IOError as e:
            self.logger.debug("chattr error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def symlink(self, target_path, path):
        self.logger.info("symlink from: to:" % (target_path, path))
        try:
            self.docker_client.symlink(target_path, path)
        except IOError as e:
            self.logger.debug("symlink error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def readlink(self, path):
        self.logger.info("readlink path" % path)
        try:
            symlink = self.docker_client.readlink(path)
        except IOError as e:
            self.logger.debug("readlink error path:%s %s" % (path, e))
            return SFTPServer.convert_errno(e.errno)
        return symlink
