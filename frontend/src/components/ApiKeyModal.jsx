import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";

function ApiKeyModal({ show, setShow, apiKeyError, handleAPIKeyModalClick }) {
  return (
    <Modal show={show} centered>
      <Modal.Header onHide={() => setShow(false)} closeButton>
        <Modal.Title>API Key</Modal.Title>
      </Modal.Header>

      <Modal.Body>
        <Form>
          <Form.Group className="mb-3" controlId="apiKeyForm.input">
            {apiKeyError && (
              <h5 className="tooltip apikey">Invalid API Key.</h5>
            )}
            <Form.Label>
              Please enter the email address listed on my public resume, which
              serves as the API key:
            </Form.Label>
            <Form.Control type="text" placeholder="API Key" autoFocus />
          </Form.Group>
        </Form>
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={() => setShow(false)}>
          Close
        </Button>
        <Button variant="primary" onClick={handleAPIKeyModalClick}>
          Confirm
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default ApiKeyModal;
