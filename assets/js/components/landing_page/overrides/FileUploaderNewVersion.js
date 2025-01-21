import React, { Component } from "react";
import PropTypes from "prop-types";
import _get from "lodash/get";
import { NewVersionButton } from "@js/invenio_rdm_records";
import { Grid, Icon, Message } from "semantic-ui-react";

export class FileUploaderNewVersion extends Component {
  render() {
    const { draft, record, isDraftRecord, filesLocked, permissions } = this.props;

    // isManaged = is managed internally by our instance (not external)
    const isDOIManaged = _get(draft, "pids.doi.provider", "") !== "external";
    const willLockFiles = isDOIManaged && isDraftRecord;

    return willLockFiles ? (
      <Grid.Row className="file-upload-note pt-5">
        <Grid.Column width={16}>
          <Message visible warning>
            <p>
              <Icon name="warning sign" />
              File addition, removal or modification are not allowed after you have
              published your upload.
            </p>
          </Message>
        </Grid.Column>
      </Grid.Row>
    ) : (
      filesLocked && (
        <Grid.Row className="file-upload-note pt-5">
          <Grid.Column width={16}>
            <Message info>
              <NewVersionButton
                record={record}
                onError={() => {}}
                className="right-floated"
                disabled={!permissions.can_new_version}
              />
              <p className="mt-5 display-inline-block">
                <Icon name="info circle" size="large" />
                You must create a new version to add, modify or delete files.
              </p>
            </Message>
          </Grid.Column>
        </Grid.Row>
      )
    );
  }
}

FileUploaderNewVersion.propTypes = {
  draft: PropTypes.object.isRequired,
  record: PropTypes.object.isRequired,
  isDraftRecord: PropTypes.bool,
  filesLocked: PropTypes.bool,
  permissions: PropTypes.object.isRequired,
}

FileUploaderNewVersion.defaultProps = {
  isDraftRecord: true,
  filesLocked: true,
}
