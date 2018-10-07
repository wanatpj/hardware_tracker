#!/usr/bin/env python3

import git
import logging
import re
import socket
import time
import urllib.request
from datetime import datetime
from optparse import OptionParser
from typing import List, Optional

class NodeTracker:
  logger = logging.getLogger("NodeTracker")
  ip_sources: List[str]
  git_uri: str
  git_path: str

  def __init__(self, ip_sources: List[str], git_uri: str, git_path: str) -> None:
    self.ip_sources = ip_sources
    self.git_uri = git_uri
    self.git_path = git_path

  def track(self) -> None:
    self._ensure_cloned()
    node_name = socket.gethostname()
    ip = self._get_extern_ip_address()
    last_ip = self._get_last_ip_address(node_name)
    if last_ip != ip:
      self._save_ip_trace(node_name, ip)
  
  def _ensure_cloned(self) -> None:
    try:
      git.Git(self.git_path).clone(self.git_uri)
    except:
      pass
  
  def _get_extern_ip_address(self):
    source_codes = self._get_source_codes()
    ips = set(
      ip
      for source in source_codes
      for ip in re.findall( r'[0-9]+(?:\.[0-9]+){3}', source)
    )
    ips_str = ",".join(ips)
    self.logger.info(f"Discovered ip: {ips_str}")
    return ips_str
  
  def _get_last_ip_address(self, node_name: str) -> Optional[str]:
    try:
      with open(node_name, "r") as file_:
        last_line = list(file_)[-1]
        return last_line[:last_line.index(" ")]
    except FileNotFoundError:
      return None
  
  def _get_source_codes(self) -> List[str]:
    return [
      urllib.request.urlopen(f"http://{url}", timeout=10).read().decode("utf-8")
      for url in self.ip_sources
    ]

  def _save_ip_trace(self, node_name: str, ip: str) -> None:
    time_ = (datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    with open(f"{self.git_path}/trace/{node_name}", "a+") as file_:
      file_.write(f"{ip} {time_}\n")
    

def _parse_flags():
  parser = OptionParser()
  parser.add_option("-i",
      "--ip_sources",
      dest="ip_sources",
      default="checkip.dyndns.org",
      help="uris to resources returning your ip addresses somewhere in html",
      metavar="URIS")
  parser.add_option("-g",
      "--git",
      dest="git",
      help="uri to git repository",
      metavar="URI")
  parser.add_option("-d",
      "--dir",
      default=".",
      dest="dir",
      help="directory where to save tracking info",
      metavar="DIR")
  (options, args) = parser.parse_args()
  return options.ip_sources.split(","), options.git, options.dir

def main():
  ip_sources, git, dir_ = _parse_flags()
  NodeTracker(ip_sources, git, dir_).track()

main()
