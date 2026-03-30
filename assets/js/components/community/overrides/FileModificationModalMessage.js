// SPDX-FileCopyrightText: 2025 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { ModalContent } from "semantic-ui-react";

const FileModificationModalMessage = () => {
  return (
    <ModalContent>
      <p>
        If you need to modify files of a record that was published more than 30 days ago, please contact our <a target="_blank" href="/support">support line</a>.
      </p>
    </ModalContent>
  )
};


export default FileModificationModalMessage;
