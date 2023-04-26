import React from "react";
import PropTypes from "prop-types";
import Dropzone from "react-dropzone";
import { humanReadableBytes } from "@js/invenio_rdm_records";
import FileTable from "./FileTable";
import { Message } from "semantic-ui-react";

const FileUploader = ({
  dropzoneParams,
  maxFileSize,
  name,
  currentFiles,
  handleDelete,
  errorMessage,
  rejectedFiles,
}) => {
  return (
    <div>
      <Dropzone {...dropzoneParams}>
        {({ getRootProps, getInputProps }) => (
          <div id="file-dropzone" {...getRootProps({ className: "dropzone" })}>
            <input {...getInputProps()} name={name} />
            <p className="ui medium header text-align-center m-0">
              Drag files here, or click to select files
            </p>
          </div>
        )}
      </Dropzone>

      <label className="helptext mt-5 mb-0">
        Optional. Max attachments size: {humanReadableBytes(maxFileSize, false)}.
        Accepted file formats: {dropzoneParams.accept}.
      </label>

      {errorMessage && (
        <Message negative>
          <p>{errorMessage}</p>
        </Message>
      )}

      {rejectedFiles.length > 0 && (
        <FileTable handleDelete={handleDelete} filesList={rejectedFiles} negative />
      )}

      {currentFiles.length > 0 && (
        <FileTable handleDelete={handleDelete} filesList={currentFiles} />
      )}
    </div>
  );
};

FileUploader.propTypes = {
  dropzoneParams: PropTypes.object.isRequired,
  maxFileSize: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  currentFiles: PropTypes.array.isRequired,
  errorMessage: PropTypes.string,
  rejectedFiles: PropTypes.array,
  handleDelete: PropTypes.func.isRequired,
};

FileUploader.defaultProps = {
  errorMessage: null,
  rejectedFiles: [],
};

export default FileUploader;
