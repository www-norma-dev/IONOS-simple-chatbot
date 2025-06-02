import * as React from "react";
import {
  Dialog,
  DialogOverlay,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface ApiKeyModalProps {
  show: boolean;
  setShow: (open: boolean) => void;
  apiKeyError: boolean;
  handleAPIKeyModalClick: () => void;
}

const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  show,
  setShow,
  apiKeyError,
  handleAPIKeyModalClick,
}) => {
  return (
    <Dialog open={show} onOpenChange={setShow}>
      <DialogOverlay />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>API Key</DialogTitle>
          {apiKeyError && (
            <p className="mt-1 text-sm text-red-600">Invalid API Key.</p>
          )}
        </DialogHeader>
        <DialogDescription className="mt-2 text-sm text-gray-700">
          Please enter the email address listed on my public resume, which
          serves as the API key:
        </DialogDescription>
        <div className="mt-3">
          <Input id="apiKeyInput" type="text" placeholder="API Key" autoFocus />
        </div>
        <DialogFooter className="mt-4 flex space-x-2">
          <Button variant="outline" onClick={() => setShow(false)}>
            Close
          </Button>
          <Button onClick={handleAPIKeyModalClick}>Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ApiKeyModal;
